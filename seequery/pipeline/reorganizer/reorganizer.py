from copy import deepcopy

from seequery.pipeline.pipeline_component import PipelineComponent
from seequery.utils.meta_template import MetaTemplateChunks


class Reorganizer(PipelineComponent):
    """ Class responsible for reorganization of outputs produced by
        previous steps. put vocabulary detected in a map where each chunk id serves
        as id for quick access. Also extract metainformation for each template to be filled.
    """
    def __init__(self) -> None:
        self.entity_sources = ['entities', 'relations']

    def process(self, data: dict) -> dict:
        """ Reorganize current outpus adding metainformation and prepare vocab map with chunk idxs as keys.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with reorganized pipeline results
        """

        data['vocab_for_templates'] = []
        for template_order_variants in data['query_templates']:
            template = template_order_variants[0]  # {TODO: argswap handling! see pattern_mapping.json}
            meta = MetaTemplateChunks.from_template(template)

            if meta.can_be_handled():
                vocab = self.make_vocab_map(data, meta)
                success = True
            else:
                vocab = dict()
                success = False

            template_fillers = {
                "meta": meta,
                "vocab": vocab,
                "success": success
            }
            data['vocab_for_templates'].append(template_fillers)

        for source in self.entity_sources:
            del data[source]

        return data

    def make_vocab_map(self, data: dict, meta: MetaTemplateChunks) -> dict:
        """ Generate a map of matches where keys are chunk idxs.

            Args:
                data (dict): a dict holding object state
                meta (MetaTemplateChunks): meta information on template

            Returns:
                dict: a dict mapping chunk idxs to vocabualry objects.
        """
        vocab_map = dict()

        for source in self.entity_sources:
            for match_item in data[source]:
                if match_item.chunk_idx in meta.chunks:
                    # vocab candidate references in the template
                    # deep copy since candidates are modified independently in different
                    # templates
                    vocab_map[match_item.chunk_idx] = deepcopy(match_item)
        return vocab_map
