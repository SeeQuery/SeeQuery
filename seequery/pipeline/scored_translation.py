from dataclasses import dataclass

from seequery.utils.linking_category import LinkingCategory


@dataclass
class ScoredTranslation:
    '''Class for keeping track of a matched ontology vocabulary'''
    score: float = 0.0
    onto_label: str = ""
    category: LinkingCategory = LinkingCategory.CLASS
