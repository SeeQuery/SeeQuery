import json
import re

from seequery.pipeline.pattern_to_template.everygram_similarity_scorer import \
    EverygramSimilarityScorer
from seequery.pipeline.pipeline_component import PipelineComponent


class PatternToTemplateSelector(PipelineComponent):
    """ Search for the closest know CQ pattern and collect SPARQL-OWL templates assigned. """
    def __init__(self, config: dict) -> None:
        self.everygram_scorer = EverygramSimilarityScorer()
        with open(config['mapping_path'], 'r') as f:
            self.pattern_mapping = json.load(f)
            self.known_patterns = self.pattern_mapping.keys()

    def process(self, data: dict) -> dict:
        """
            A method processing given data with current pipeline step.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with current pipeline results
        """
        data['cq_pattern'] = self.construct_cq_pattern(data)
        data['cq_pattern'] = self.drop_auxiliary_if_pc_detected(data['cq_pattern'])
        data['cq_pattern'] = self.drop_question_mark(data['cq_pattern'])

        data['closest_pattern'] = self.get_closest_match(data['cq_pattern'])
        data['query_templates'] = self.pattern_mapping[data['closest_pattern']]
        return data

    def construct_cq_pattern(self, data: dict) -> str:
        """ Drop auxiliary verbs from pattern.

        Args:
            data (dict): input data holding info from previous processing steps

        Returns:
            str: CQ pattern constructed.
        """
        cq = data['cq']
        all_vocab = \
            sorted(data['entities'] + data['relations'], key=lambda x: x.char_begin, reverse=True)

        cq_pattern = cq
        for item in all_vocab:
            cq_pattern = f'{cq_pattern[:item.char_begin]}{item.chunk_idx}{cq_pattern[item.char_end:]}'
        return cq_pattern

    def drop_auxiliary_if_pc_detected(self, cq_pattern: str) -> str:
        """ Drop auxiliary verbs from pattern.

        Args:
            pattern (str): CQ pattern

        Returns:
            str: CQ patterns with auxiliary verbs removed.
        """
        regex = (r'\b([Ii]s|[Aa]m|[Aa]re|[Hh]ave|[Hh]as|[Dd]id|[Ww]ould'
                 r'|[Ww]ill|[Ss]hould|[Cc]an|[Mm]ay|[Mm]ust|[Nn]eed|[Ss]hall)\b ')
        if 'PC1' in cq_pattern:
            cq_pattern = re.sub(regex, '', cq_pattern)
        return cq_pattern

    def drop_question_mark(self, cq_pattern: str) -> str:
        """ Drop question mark from a CQ pattern.

        Args:
            cq_pattern (str): CQ pattern

        Returns:
            str: CQ pattern without question mark at the end
        """
        return re.sub(r"\?$", "", cq_pattern)

    def get_closest_match(self, pattern: str) -> str:
        """ Get closest know CQ pattern.

        Args:
            pattern (str): CQ pattern extracted

        Returns:
            str: closest CQ pattern selected
        """
        max_ec = self._get_max_chunk_id(pattern, "EC")
        max_pc = self._get_max_chunk_id(pattern, "PC")

        # consider only those patterns with same EC/PC number
        valid_matches = []
        for known_pattern in self.known_patterns:
            known_max_ec = self._get_max_chunk_id(known_pattern, "EC")
            known_max_pc = self._get_max_chunk_id(known_pattern, "PC")
            if max_ec == known_max_ec and max_pc == known_max_pc:
                valid_matches.append(known_pattern)

        # search for closest pattern using an anygram jaccard similarity
        best_match = ""
        best_score = 0.0

        for known_pattern in valid_matches:
            score = self.everygram_scorer.score(pattern, known_pattern)
            if score > best_score:
                best_score = score
                best_match = known_pattern
        return best_match

    def _get_max_chunk_id(self, pattern: str, chunk: str) -> int:
        """ Get max id assigned to a given chunk type.

        Args:
            pattern (str): pattern to search in
            chunk (str): chunk type (EC/PC)

        Returns:
            int: max id assigned to a given chunk type (EC/PC)
        """
        max_idx = 0

        for m in re.finditer(rf'\b{chunk}[0-9]+\b', pattern):
            curent_idx = int(m.group()[-1])
            if curent_idx > max_idx:
                max_idx = curent_idx

        return max_idx
