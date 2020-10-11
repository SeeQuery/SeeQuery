from typing import List

from seequery.pipeline.match_item import MatchItem
from seequery.pipeline.pipeline_component import PipelineComponent
from seequery.utils.helpers import Helpers


class Merger(PipelineComponent):
    def __init__(self) -> None:
        pass

    def process(self, data: dict) -> dict:
        """
            Merge ReqTagger and Direct Matcher outputs.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with current pipeline results
        """
        types = ['entities', 'relations']
        cq = data['cq']

        merged_phrases = []

        for key in types:
            potential = data['potential_matches'][key]
            direct = data['direct_matches'][key]

            for p in potential:
                span_potential = (p.char_begin, p.char_end)

                current_potential_overlaps = False
                for d in direct:
                    span_direct = (d.char_begin, d.char_end)

                    if Helpers.span_overlap(span_potential, span_direct):
                        merged = d
                        merged.char_begin = min(p.char_begin, d.char_begin)
                        merged.char_end = max(p.char_end, d.char_end)
                        merged.text = cq[merged.char_begin:merged.char_end]
                        merged_phrases.append(merged)
                        current_potential_overlaps = True
                        break

                if not current_potential_overlaps:
                    merged_phrases.append(p)

            for d in direct:
                span_direct = (d.char_begin, d.char_end)
                current_direct_overlaps = False

                for p in potential:
                    span_potential = (p.char_begin, p.char_end)
                    if Helpers.span_overlap(span_potential, span_direct):
                        current_direct_overlaps = True
                        break

                if not current_direct_overlaps:
                    print(f"\tDirect {d.raw_text} did not intersect adding as is")
                    merged_phrases.append(d)

        # categorize based on is_ec attrib, sort by position in cq
        data['entities'] = sorted([e for e in merged_phrases if e.is_ec], key=lambda x: x.char_begin)
        data['relations'] = sorted([e for e in merged_phrases if not e.is_ec], key=lambda x: x.char_begin)

        for dataset, prefix in [('entities', 'EC'), ('relations', 'PC')]:
            data[dataset] = self.assign_chunk_ids(data[dataset], prefix)

        del data['potential_matches']
        del data['direct_matches']
        return data

    def assign_chunk_ids(self, matches: List[MatchItem], label_prefix: str) -> List[MatchItem]:
        """ Assign each mach chunk (EC{NUM}/PC{NUM}).

        Args:
            matches (List[MatchItem]): matches to assign ids to
            label_prefix (str): label prefix to be used

        Returns:
            matches (List[MatchItem]): matches with ids
        """
        for idx, match_item in enumerate(matches):
            match_item.chunk_idx = f"{label_prefix}{idx+1}"
        return matches
