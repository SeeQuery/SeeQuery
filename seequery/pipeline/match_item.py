from dataclasses import dataclass, field
from typing import List
from seequery.pipeline.scored_translation import ScoredTranslation


@dataclass
class MatchItem:
    '''Class for keeping track of a match'''
    char_begin: int = 0
    char_end: int = 0
    raw_text: str = ""
    normalized_text: str = ""
    # see docs.python.org/3/library/dataclasses.html#mutable-default-values
    scored_candidates: List[ScoredTranslation] = field(default_factory=list)
    is_ec: bool = False
    is_explicit_match: bool = False
    chunk_idx: str = ""
