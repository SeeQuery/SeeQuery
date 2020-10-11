import logging

import spacy

from seequery.embeddings.embeddings_manager import EmbeddingsManager
from seequery.ontology.ontology_manager import OntologyManager
from seequery.pipeline.linker.entity_linker import EntityLinker
from seequery.pipeline.pattern_to_template.pattern_to_template_selector import \
    PatternToTemplateSelector
from seequery.pipeline.query_filler.query_filler import QueryFiller
from seequery.pipeline.reorganizer.reorganizer import Reorganizer
from seequery.pipeline.vocab.direct_matcher import DirectMatcher
from seequery.pipeline.vocab.merger import Merger
from seequery.pipeline.vocab.reqtagger import ReqTagger
from seequery.utils.helpers import Helpers


class Pipeline:
    """ A class defining pipeline steps to be run to create queries. """
    def __init__(self, config: dict, embedding_mngr: EmbeddingsManager,
                 onto_mngr: OntologyManager, spacy_nlp: spacy.lang.xx.Language):
        """ Initialize processing pipeline.

        Args:
            config (dict): Pipeline config dict
            embedding_mngr (EmbeddingManager): Embedding manager object
            onto_mngr (OntologyManager): Ontology manager object.
            spacy_nlp (Any): callback to a spacy processor
        """

        self.config = config
        self.embedding_mngr = embedding_mngr
        self.ontology_mngr = onto_mngr
        self.spacy_nlp = spacy_nlp
        self.components = [
            ReqTagger(spacy_nlp, self.ontology_mngr),
            DirectMatcher(self.ontology_mngr),
            Merger(),  # helper step, merging ReqTagger and Direct Matcher outputs
            PatternToTemplateSelector(config['pattern_extractor']),
            Reorganizer(),  # prepares data for further processing, auxiliary step
            EntityLinker(self.ontology_mngr, self.embedding_mngr, config['entity_linker']),
            QueryFiller(self.ontology_mngr)
        ]

    def run(self, cq: str) -> dict:
        """ Process CQ with the pipeline.

            Args:
                cq (str): Competency Question as string

            Returns:
                processing_data (dict): dict with all produced components outputs

        """
        cq = Helpers.clean_cq(cq)
        logging.debug(f"Pipeline::run preprocessing, cq cleaned {cq}")

        data = {"cq": cq}
        try:
            for component in self.components:
                data = component.process(data)
        except Exception:
            return {"QueryGenerationFailure": "Cannot generate a query from given CQ/ontology."}
        return data
