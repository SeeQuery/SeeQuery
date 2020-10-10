from typing import List
from seequery.pipeline.linker.contextual_rescorer import ContextualRescorer
from seequery.pipeline.match_item import MatchItem
from seequery.pipeline.scored_translation import ScoredTranslation
from seequery.utils.helpers import Helpers
from seequery.utils.linking_category import LinkingCategory
from seequery.utils.meta_template import MetaTemplateChunks
from seequery.pipeline.pipeline_component import PipelineComponent
from seequery.ontology.ontology_manager import OntologyManager
from seequery.embeddings.embeddings_manager import EmbeddingsManager


class EntityLinker(PipelineComponent):
    """ Linking phrases from a CQ to ontology vocabulary. """
    def __init__(self, ontology_mngr: OntologyManager, embeddings_mngr: EmbeddingsManager,
                 config: dict) -> None:
        self.ontology_mngr = ontology_mngr
        self.embeddings_mngr = embeddings_mngr
        self.config = config
        self.contextual_rescorer = ContextualRescorer(self.ontology_mngr, self.embeddings_mngr)

    def process(self, data: dict) -> dict:
        """ A method processing given data with current pipeline step.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with current pipeline results
        """
        for meta_enriched_vocab in data['vocab_for_templates']:
            meta = meta_enriched_vocab['meta']
            limit_entities = self.config['best_mappings'] if len(meta.relations) > 0 else 1

            if meta_enriched_vocab['success']:
                for chunk_idx, match_item in meta_enriched_vocab['vocab'].items():
                    if not match_item.is_explicit_match:
                        category = self._get_category(chunk_idx, meta)
                        match_item.scored_candidates = self.link_item_translations(
                            match_item, category, limit_entities)

        data = self.contextual_rescorer.process(data)
        return data

    def link_item_translations(self, item: MatchItem, category: LinkingCategory,
                               limit: int) -> List[ScoredTranslation]:
        """ Attach possible translations above threshold and sort them in descending order.

            Args:
                item (MatchItem): item to assign translations
                category (LinkingCategory): category of current item
                limit (int): how many top tranlations to preserve

            Returns:
                List[ScoredTranslation]: a list of translations proposed
        """
        translations: List[ScoredTranslation] = []

        for label in self.ontology_mngr.onto_map[category]:
            normalized_label = Helpers.normalize_label(label)
            score = self.embeddings_mngr.phrase_similarity(item.normalized_text, normalized_label)

            if self._similarity_over_threshold(category, score):
                translations.append(ScoredTranslation(score=score, onto_label=label, category=category))
        translations = sorted(translations, key=lambda x: x.score, reverse=True)[:limit]
        return translations

    def _similarity_over_threshold(self, category: LinkingCategory, score: float) -> bool:
        """ Check if calculated similarity falls above the expected threshold.

            Args:
                category (LinkingCategory): category of current item
                score (float): translation similarity score

            Returns:
                bool: True if a translation scores over the threshold
        """
        if category in [LinkingCategory.INDIVIDUAL, LinkingCategory.CLASS]:
            if score >= self.config['min_entity_similarity']:
                return True
            else:
                return False
        elif category in [LinkingCategory.DATA_PROPERTY, LinkingCategory.OBJECT_PROPERTY]:
            if score >= self.config['min_relation_similarity']:
                return True
            else:
                return False
        return True

    def _get_category(self, chunk_idx: str, meta_template: MetaTemplateChunks) -> LinkingCategory:
        """ Check category of a given chunk_idx.

            Args:
                chunk_idx (str): chunk index to be verified
                meta_template (MetaTemplateChunks): translation meta information

            Returns:
                LinkingCategory: Category the chunk idx falls into.
        """
        if chunk_idx in meta_template.object_property_chunks:
            return LinkingCategory.OBJECT_PROPERTY
        elif chunk_idx in meta_template.data_property_chunks:
            return LinkingCategory.DATA_PROPERTY
        else:
            return LinkingCategory.CLASS
