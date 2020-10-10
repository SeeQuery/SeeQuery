from seequery.utils.helpers import Helpers
from seequery.ontology.ontology_manager import OntologyManager
from seequery.pipeline.match_item import MatchItem
from seequery.pipeline.scored_translation import ScoredTranslation
from seequery.utils.linking_category import LinkingCategory
from seequery.pipeline.pipeline_component import PipelineComponent
import re
from typing import Dict, List, Tuple


class DirectMatcher(PipelineComponent):
    def __init__(self, ontology_mngr: OntologyManager) -> None:
        self.ontology_mngr = ontology_mngr

    def process(self, data: dict) -> dict:
        """
            A method processing given data with current pipeline step.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with current pipeline results
        """
        cq = data['cq'].lower()
        result: Dict[str, List[MatchItem]] = {'entities': [], 'relations': []}

        spans_generated: List[Tuple[int, int]] = []

        for category in self.ontology_mngr.onto_map:
            labels_available = list(self.ontology_mngr.onto_map[category].keys())
            labels_from_longest = sorted(labels_available, key=len, reverse=True)

            for label in labels_from_longest:
                normalized_label = Helpers.normalize_label(label).lower()
                label_lower = label.lower()
                r = rf'\b({re.escape(normalized_label)}|{re.escape(label_lower)})(ing|ed|es|s)?\b'

                for m in re.finditer(r, cq):
                    current_span = (m.span()[0], m.span()[1])
                    if any([Helpers.is_subspan(current_span, s) for s in spans_generated]):
                        continue
                    ec = True if category in [LinkingCategory.CLASS, LinkingCategory.INDIVIDUAL] else False
                    key = 'entities' if ec else 'relations'
                    result[key].append(MatchItem(char_begin=m.span()[0],
                                                 char_end=m.span()[1],
                                                 raw_text=m.group(),
                                                 normalized_text=m.group(),
                                                 is_ec=ec,
                                                 is_explicit_match=True,
                                                 scored_candidates=[ScoredTranslation(
                                                    score=1.0,
                                                    onto_label=label,
                                                    category=category
                                                 )]))
                    spans_generated.append(current_span)
        data['direct_matches'] = result
        return data
