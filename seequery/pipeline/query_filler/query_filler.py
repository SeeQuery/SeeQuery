from operator import itemgetter
from typing import Dict, List
from seequery.pipeline.match_item import MatchItem
from seequery.pipeline.pipeline_component import PipelineComponent
from seequery.ontology.ontology_manager import OntologyManager
import re


class QueryFiller(PipelineComponent):
    """ Fill query template with actual IRIs """
    def __init__(self, ontology_manager: OntologyManager):
        self.ontology_mngr = ontology_manager

    def process(self, data: dict) -> dict:
        """
            A method processing given data with current pipeline step.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with current pipeline results
        """
        queries = []
        for idx, meta_enriched_vocab in enumerate(data['vocab_for_templates']):
            if not meta_enriched_vocab['success']:
                data['queries'].append("")
                continue

            query_variants = data['query_templates'][idx]
            swap = True if 'swap' in meta_enriched_vocab and meta_enriched_vocab['swap'] else False

            template = self.choose_template_variant(query_variants, swap)
            queries.append(self.fill_template(template, meta_enriched_vocab['vocab']))

        data['queries'] = queries
        return data

    def fill_template(self, template: str, vocab: Dict[str, MatchItem]) -> str:
        """ Fill templates with IRIs

        Args:
            template (str): Template to be filled
            vocab (Dict[str, MatchItem]): each chunk translation information

        Returns:
            str: template filled with IRIs
        """
        chunk_spans = []
        for m in re.finditer("<(IS_EC|HAS_EC|EC|PC)[0-9]+>", template):
            # store where chunk starts, ends and what is the chunk_idx (withiout angle brackets)
            chunk_spans.append(
                (m.span()[0], m.span()[1], m.group()[1:-1]))

        chunk_spans = sorted(chunk_spans, key=itemgetter(0), reverse=True)  # sort from the latest

        for begin, end, chunk_idx in chunk_spans:
            # if HAS_EC{n} or IS_EC{n} seen in property
            if chunk_idx[:-1] not in ['PC', 'EC']:
                chunk_idx = chunk_idx.split("_")[1]  # get id after prefix

            match_item = vocab[chunk_idx]
            onto_label = match_item.scored_candidates[0].onto_label
            category = match_item.scored_candidates[0].category
            onto_iri = self.ontology_mngr.onto_map[category][onto_label].iri

            template = template[:begin] + "<" + onto_iri + ">" + template[end:]
        return template

    def choose_template_variant(self, variants: List[str], argswap: bool) -> str:
        """ If multiple SPARQL-OWL query template variants provided, choose appropriate based on 'argswap'

        Args:
            variants (List[str]): List of template variants
            argswap (bool): are arguments swapped?

        Returns:
            str: variant chosen
        """
        if len(variants) == 1:
            return variants[0]
        else:
            return variants[1] if argswap else variants[0]
