import re
from typing import List, Tuple

import spacy

from seequery.ontology.ontology_manager import OntologyManager
from seequery.pipeline.match_item import MatchItem
from seequery.pipeline.pipeline_component import PipelineComponent
from seequery.utils.helpers import Helpers


class ReqTagger(PipelineComponent):
    NON_RELATION_THING = ['is', '’s', 'are', 'was', 'do', 'does', 'did', 'were',
                          'have', 'had', 'can', 'could', 'regarding',
                          'is of', 'are of', 'are in', 'given', 'is there', 'has']

    NON_ENTITY_THINGS = ['a kind', 'the kind', 'kind', 'kinds', 'the kinds',
                         'category', 'a category', 'the category', 'categories', 'the categories',
                         'type', 'a type', 'the type', 'sort', 'types', 'the types']

    RULES_RELATIONS = [
        ['{1+}JJ', 'IN'],
        ['JJR', 'IN'],
        ['RB', 'VBD'],
        ['{0+}MD', '{1+}VBZ|VBN', 'TO', 'VB'],
        ['{0+}MD', 'VB', 'VBN', 'IN'],
        ['{1?}TO', 'VB|VBN|VBZ|VBP', '{1?}JJ', 'IN'],
        ['{0+}VB|MD', '{0+}TO', 'VB'],
        ['{1?}TO', '{0+}VB|VBP|VBZ|VBN|VBD|VBG', '{1+}RBS|VB|VBZ|VBN|VBD|VBG|IN', 'RBS|IN'],
        ['{1?}TO', 'VB|VBZ|VBP|VBG|VBD', 'VB|VBN|VBG|VBG|VBD|JJR|RP'],
        ['VBN', 'VBG']
    ]

    RULES_ENTITIES = [
        ['{1?}DT', '{0+}FW|JJ|JJS|NN|NNS|NNP', 'NN|NNP|NNS'],
        ['DT', 'VB|VBG|VBD|VBZ|VBN', '{0+}NN|NNS|NNP|JJ', 'NN|NNS|NNP']
    ]

    def __init__(self, nlp: spacy.lang.xx.Language, ontology_mngr: OntologyManager) -> None:
        self.nlp = nlp
        self.ontology_mngr = ontology_mngr
        for idx in range(len(self.RULES_RELATIONS)):
            self.RULES_RELATIONS[idx] = ['{1?}AUX|VBP'] + self.RULES_RELATIONS[idx]

    def parse_rule(self, rule: List[str]) -> str:
        """ Parse rule expressed as list of tokens into internal representation.

        Args:
            rule (List[str]): rule as a list of requirements.

        Returns:
            str: parsed rule.
        """
        return r''.join(self.parse_item(item) for item in rule)

    def parse_item(self, item: str) -> str:
        postfix = ""
        if item.startswith("{"):
            if item.startswith('{0+}'):
                postfix = '*'
            elif item.startswith('{1+}'):
                postfix = '+'
            elif item.startswith('{1?}'):
                postfix = '?'
            item = item[4:]
        return rf"([0-9]+::({item}),?){postfix}"

    def find_matching_spans(self, doc: spacy.tokens.doc.Doc, rules: List[List[str]],
                            rejected: List[str], cq: str) -> List[Tuple[int, int]]:
        """ Find spans matching rules.

        Args:
            doc (spacy.tokens.doc.Doc): spacy tokenized document
            rules (List[List[str]]): rules to be used
            rejected (List[str]): phrases to be rejected
            cq (str): cq to be processed

        Returns:
            List[Tuple[int, int]]: list of spans

        """
        spans = []
        pos_text = ",".join(
            ["{i}::{pos}".format(i=i, pos=t.tag_) for i, t in enumerate(doc)])

        for rule in rules:  # try to extract chunks
            rule_parsed = self.parse_rule(rule)
            for m in re.finditer(rule_parsed, pos_text):
                id_tags = [elem for elem in m.group().split(",") if elem != '']
                ids = [int(id_tag.split("::")[0]) for id_tag in id_tags]
                span = (doc[ids[0]].idx, doc[ids[-1]].idx + len(doc[ids[-1]]))
                if cq[span[0]:span[1]].lower() not in rejected:
                    spans.append(span)
        return Helpers.filter_subspans(spans)

    def process(self, data: dict) -> dict:
        """
            A method processing given data with current pipeline step.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with current pipeline results
        """
        cq = data['cq']
        doc = self.nlp(cq.lower())
        entity_spans = self.find_matching_spans(doc, self.RULES_ENTITIES, self.NON_ENTITY_THINGS, cq)
        relations_spans = self.find_matching_spans(doc, self.RULES_RELATIONS, self.NON_RELATION_THING, cq)

        entities = []
        for begin, end in entity_spans:
            normalized_text = \
                re.sub(r'^([Tt]he|[Aa]|[Ss]ome|[Gg]iven|different|many|various|all|much) ',
                       '', cq[begin:end].strip())

            entities.append(MatchItem(char_begin=begin, char_end=end,
                                      raw_text=cq[begin:end],
                                      normalized_text=normalized_text,
                                      is_ec=True,
                                      is_explicit_match=False))

        relations = []
        for begin, end in relations_spans:
            normalized_text = \
                re.sub(
                    r'^(is|are|was|will|have|has|had|should|shall|would|can|could) ',
                    '', cq[begin:end].strip())
            relations.append(MatchItem(char_begin=begin, char_end=end,
                                       raw_text=cq[begin:end],
                                       normalized_text=normalized_text,
                                       is_ec=False,
                                       is_explicit_match=False))

        data['potential_matches'] = {"entities": entities, "relations": relations}
        return data
