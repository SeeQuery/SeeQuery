from typing import List

from seequery.embeddings.embeddings_manager import EmbeddingsManager
from seequery.ontology.ontology_manager import OntologyManager
from seequery.pipeline.linker.contextual_rescorer import ContextualRescorer
from seequery.pipeline.match_item import MatchItem
from seequery.pipeline.pipeline_component import PipelineComponent
from seequery.pipeline.scored_translation import ScoredTranslation
from seequery.utils.helpers import Helpers
from seequery.utils.linking_category import LinkingCategory
from seequery.utils.meta_template import MetaTemplateChunks
import re


class EntityLinker(PipelineComponent):
    """ Linking phrases from a CQ to ontology vocabulary. """
    def __init__(self, ontology_mngr: OntologyManager, embeddings_mngr: EmbeddingsManager, spacy_nlp,
                 config: dict) -> None:
        self.ontology_mngr = ontology_mngr
        self.embeddings_mngr = embeddings_mngr
        self.config = config
        self.spacy_nlp = spacy_nlp
        self.contextual_rescorer = ContextualRescorer(self.ontology_mngr, self.embeddings_mngr)
        self.labels_to_normalized, self.normalized_to_labels = self._normalize_labels()

    def process(self, data: dict) -> dict:
        """ A method processing given data with current pipeline step.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with current pipeline results
        """

        if 'status' in data and data['status']['type'] == 'ERROR':
            return data

        errors = []

        for meta_enriched_vocab in data['vocab_for_templates']:
            meta = meta_enriched_vocab['meta']
            limit_entities = self.config['best_mappings'] if len(meta.relations) > 0 else 1

            if meta_enriched_vocab['success']:
                vectorized_labels = self._vectorize_labels(data['cq'])
                for chunk_idx, match_item in meta_enriched_vocab['vocab'].items():
                    if not match_item.is_explicit_match:
                        category = self._get_category(chunk_idx, meta)
                        match_item.scored_candidates = self.link_item_translations(
                            match_item, category, limit_entities, data['cq'], vectorized_labels)
                        if len(match_item.scored_candidates) == 0:
                            errors.append(match_item.normalized_text)

        if len(errors) > 0:
            data['status'] = {"type": "ERROR", "message": f"No translations for {', '.join(list(set(errors)))}"}
        else:
            data = self.contextual_rescorer.process(data)
        return data

    def link_item_translations(self, item: MatchItem, category: LinkingCategory,
                               limit: int, cq: str, vectorized_labels) -> List[ScoredTranslation]:
        """ Attach possible translations above threshold and sort them in descending order.

            Args:
                item (MatchItem): item to assign translations
                category (LinkingCategory): category of current item
                limit (int): how many top tranlations to preserve

            Returns:
                List[ScoredTranslation]: a list of translations proposed
        """
        translations: List[ScoredTranslation] = []

        match_lemma = " ".join([t.lemma_ for t in self.spacy_nlp(item.normalized_text.lower())])

        for label in vectorized_labels[category]:
            normalized_label = self.labels_to_normalized[category][label]
            label_lemma = " ".join([t.lemma_ for t in self.spacy_nlp(normalized_label.lower())])
            if item.normalized_text.lower() == normalized_label.lower() or label_lemma == match_lemma or Helpers.strip_s(item.normalized_text.lower()) == Helpers.strip_s(normalized_label.lower()):
                return [ScoredTranslation(score=1.0, onto_label=label, category=category)]
            else:
                if re.search(f"\b{item.normalized_text.lower()}\b", f"\b{normalized_label.lower()}\b") or re.search(f"\b{match_lemma}\b", f"\b{label_lemma}\b"):
                    score = 1.0
                else:
                    context = cq.lower() + ", how about " + item.normalized_text + "?"
                    v = self.embeddings_mngr.vectorize(item.normalized_text, context)
                    score = self.embeddings_mngr.cos(v, vectorized_labels[category][label])

                    # score = self.embeddings_mngr.similarity(item.normalized_text, normalized_label, cq)

            if self._similarity_over_threshold(category, score):
                translations.append(ScoredTranslation(score=score, onto_label=label, category=category))
        translations = sorted(translations, key=lambda x: x.score, reverse=True)[:limit]
        return translations

    def _vectorize_labels(self, context):
        context = context.lower()
        vectorized_labels = dict()
        for category in self.ontology_mngr.onto_map:
            vectorized_labels[category] = dict()
            for label in self.ontology_mngr.onto_map[category]:
                normalized_label = Helpers.normalize_label(label)
                extended_context = context + ", how about " + normalized_label + "?"
                vectorized_labels[category][label] = self.embeddings_mngr.vectorize(normalized_label, extended_context)
        return vectorized_labels

    def _normalize_labels(self):
        labels_to_normalized = dict()
        normalized_to_label = dict()
        for category in self.ontology_mngr.onto_map:
            labels_to_normalized[category] = dict()
            normalized_to_label[category] = dict()
            for label in self.ontology_mngr.onto_map[category]:
                labels_to_normalized[category][label] = Helpers.normalize_label(label)
                normalized_to_label[category][Helpers.normalize_label(label)] = label
        return labels_to_normalized, normalized_to_label

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
