from seequery.pipeline.pipeline_component import PipelineComponent
from seequery.pipeline.scored_translation import ScoredTranslation
from seequery.ontology.ontology_manager import OntologyManager
from seequery.embeddings.embeddings_manager import EmbeddingsManager
from seequery.utils.meta_template import MetaTemplateChunks
from seequery.pipeline.match_item import MatchItem
from typing import Any, Dict, List, Optional, Tuple
import itertools
import numpy as np


class ContextualRescorer(PipelineComponent):
    """ Having possible translation, score them according to their coexistence. """
    def __init__(self, ontology_manager: OntologyManager, embeddings_mngr: EmbeddingsManager) -> None:
        self.ontology_mngr = ontology_manager
        self.embeddings_mngr = embeddings_mngr

    def process(self, data: dict) -> dict:
        """
            A method processing given data with current pipeline step.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with current pipeline results
        """
        for meta_enriched_vocab in data['vocab_for_templates']:
            meta_enriched_vocab['swap'] = False

            if not meta_enriched_vocab['success']:
                continue

            if len(meta_enriched_vocab['meta'].relations) == 0:
                for chunk_idx, match_item in meta_enriched_vocab['vocab'].items():
                    match_item.scored_candidates = self.get_top_translations(match_item.scored_candidates)
            else:
                result, swap = self.get_best_combination(meta_enriched_vocab)
                pred_idx, lhs_idx, rhs_idx = self._get_required_idxs(meta_enriched_vocab['meta'])

                to_update = [(pred_idx, "best_property"), (lhs_idx, "best_lhs")]
                if rhs_idx:
                    to_update.append((rhs_idx, "best_rhs"))

                for idx, key in to_update:
                    meta_enriched_vocab['vocab'][idx].scored_candidates = [result[key]['scored_translation']]
                if swap:
                    meta_enriched_vocab['swap'] = True
        return data

    def get_best_combination(self, meta_enriched_vocab: dict) -> Tuple[dict, Optional[bool]]:
        """ Get best combination.

            Args:
                meta_entriched_vocab (dict): extracted phrases and template metadata

            Returns:
                Tuple[dict, bool]: Best combination with argswitch info
        """
        best_property = None
        best_lhs = None
        best_rhs = None

        best_score = 0.0
        best_arg_swap = None

        for relation, lhs, rhs in self._construct_all_possible_connections(meta_enriched_vocab):
            # verify domain range restrictions
            relation_obj, relation_st = relation
            lhs_obj, lhs_st = lhs
            rhs_obj, rhs_st = rhs

            restriction_score, restriction_arg_swap = \
                self.ontology_mngr.calc_restriction_score(relation_obj, lhs_obj, rhs_obj)
            if restriction_score < 1.0:  # these candidates cannot be used together, skip
                continue

            scores = [relation_st.score, lhs_st.score]
            if rhs_st:
                scores.append(rhs_st.score)

            avg_translation_score = np.mean(scores)

            usage_score, usage_arg_swap = self.ontology_mngr.calc_usage_score(
                relation_obj, lhs_obj, rhs_obj)

            if restriction_arg_swap:
                arg_swap = restriction_arg_swap
            elif usage_arg_swap:
                arg_swap = usage_arg_swap
            else:
                arg_swap = False

            combined_score = 0.6 * avg_translation_score + 0.4 * usage_score

            if combined_score > best_score:
                best_score = combined_score
                best_arg_swap = arg_swap
                best_property = relation
                best_lhs = lhs
                best_rhs = rhs

        result = {}
        if best_property:
            result['best_property'] = {"obj": best_property[0], "scored_translation": best_property[1]}
        if best_lhs:
            result['best_lhs'] = {"obj": best_lhs[0], "scored_translation": best_lhs[1]}
        if best_rhs:
            result["best_rhs"] = {"obj": best_rhs[0], "scored_translation": best_rhs[1]}
        else:
            result["best_rhs"] = {"obj": None, "scored_translation": None}
        return result, best_arg_swap

    def _construct_all_possible_connections(self, meta_enriched_vocab: dict) -> Any:
        """ Construct all possible property and arguments translations.

            Args:
                meta_entriched_vocab (dict): extracted phrases and template metadata

            Returns:
                Any: An iterator over possible combinations
        """
        meta = meta_enriched_vocab['meta']
        vocab = meta_enriched_vocab['vocab']

        prop_idx, lhs_idx, rhs_idx = self._get_required_idxs(meta)

        property_translations = self._collect_ontology_objects(vocab, prop_idx)
        lhs_translations = self._collect_ontology_objects(vocab, lhs_idx)
        rhs_translations = self._collect_ontology_objects(vocab, rhs_idx) if rhs_idx else [(None, None)]

        return itertools.product(property_translations, lhs_translations, rhs_translations)

    def _get_required_idxs(self, meta: MetaTemplateChunks) -> Tuple[str, str, Optional[str]]:
        """ Get idxes for further processing.

            Args:
                meta (MetaTemplateChunks): meta information on template

            Returns:
                Tuple[str, str, Optional[str]]: List of chunk idxes
        """
        prop_idx = list(meta.relations)[0]
        entity_idxs = sorted(list(meta.entities))
        lhs_idx = entity_idxs[0]
        rhs_idx = entity_idxs[1] if len(entity_idxs) >= 2 else None
        return (prop_idx, lhs_idx, rhs_idx)

    def _collect_ontology_objects(self, vocab: Dict[str, MatchItem],
                                  chunk_idx: str) -> List[Tuple[Any, Optional[ScoredTranslation]]]:
        """ Get ontology objects from tranlations.

            Args:
                vocab (Dict[str, MatchItem]): chunk ids mapped to extracted vocab
                chunk_idx (str): idx of a chunk to be processed

            Returns:
                List[Tuple[Any, ScoredTranslation]]: List of objects assigned to a given chunk
        """
        objects: List[Tuple[Any, Optional[ScoredTranslation]]] = []
        for scored_translation in vocab[chunk_idx].scored_candidates:
            objects.append(
                (self.ontology_mngr.onto_map[scored_translation.category][scored_translation.onto_label],
                 scored_translation)
            )
        return objects

    def get_top_translations(self, scored_candidates: List[ScoredTranslation],
                             count: int = 1) -> Optional[List[ScoredTranslation]]:
        """ Get top /count/ scored translations.

            Args:
                scored candidates (List[ScoredTranslation]): a list of tranlations to extract from

            Returns:
                Optional[List[ScoredTranslation]]: top /count/ translations.
                                                   None if no translations available
        """
        if len(scored_candidates) > 0:
            return scored_candidates[:count]
        else:
            return None
