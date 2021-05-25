from seequery.pipeline.pipeline_component import PipelineComponent

from transformers import BertTokenizer, BertModel
from typing import List, Optional, Tuple
import torch


class BertVectorizer(PipelineComponent):
    ''' Use pretrained BERT model to vectorize phrases in contexts and provide
        API to calculate similarity between phrases as well as choosing
        the most similar phrases among ontology vocabulary.
    '''

    def __init__(self, model='bert-base-uncased', print_debug_info=False, ontology_mngr=None):
        self.tokenizer = BertTokenizer.from_pretrained(model)
        self.print_debug_info = print_debug_info
        self.model = BertModel.from_pretrained(model, return_dict=True)
        self.model.eval()
        self.cos = torch.nn.CosineSimilarity()
        self.ontology_mngr = ontology_mngr

    def process(self, data: dict) -> dict:
        cq = data['cq']
        entities = [e.normalized_text for e in data['entities']]
        relations = [r.normalized_text for r in data['relations']]

        for entity in entities:


            print(f'{entity}\t{self.rank_similarities(entity, cq, self.ontology_mngr.entities)[:5]}')
        for relation in relations:
            print(f'{relation}\t{self.rank_similarities(relation, cq, self.ontology_mngr.properties)[:5]}')
        return data

    def log(self, message):
        ''' simple logging function.
            Set print_debug_info to true to enable logging. '''
        if self.print_debug_info:
            print(message)

    def vectorize(self, focus: str, context: str = ""):
        ''' Create an embedding of focus (a phrase being a part of a broader context) being aware of the context it was used into. '''
        alignment = self.find_alignment(context,
                                        focus)  # check where the focus (phrase) is located inside of the context
        tokens = torch.tensor([self.tokenize(context)])  # transform context into a tensor of token ids
        segments = torch.tensor([[1] * len(tokens[0])])  # mark whole context as a single sentence (required by BERT)

        with torch.no_grad():
            outputs = self.model(tokens, segments)  # run BERT
            batch = outputs['last_hidden_state'][0]  # extract first batch
            phrase_vectors = batch[alignment[0]:alignment[1]]  # extract embeddings related to focus (phrase)
            return torch.mean(phrase_vectors, dim=0, keepdims=True)  # apply mean pooling of embeddings from a phrase

    def find_alignment(self, context: str, phrase: str) -> Optional[Tuple[int, int]]:
        ''' Check at what offsets a given phrase begins and ends inside of a context. '''
        tokenized_context = self.tokenize(context)
        tokenized_phrase = self.tokenize(phrase, add_specials=False)
        start = self._find_align_start(tokenized_context, tokenized_phrase)
        if start == -1:
            return None
        end = start + len(tokenized_phrase)
        return (start, end)

    def tokenize(self, text, add_specials=True) -> List[int]:
        ''' Convert text into a sequence of token ids '''
        if add_specials:
            text = "[CLS] " + text + " [SEP]"

        tokens = self.tokenizer.tokenize(text)
        self.log(f"Tokenized text: {tokens}")
        return self.tokenizer.convert_tokens_to_ids(tokens)

    def _find_align_start(self, haystack, needle):
        """Return the index at which the sequence needle appears in the
        sequence haystack, or -1 if it is not found, using the Boyer-
        Moore-Horspool algorithm. The elements of needle and haystack must
        be hashable.

        >>> find([1, 1, 2], [1, 2])
        1

        """
        h = len(haystack)
        n = len(needle)
        skip = {needle[i]: n - i - 1 for i in range(n - 1)}
        i = n - 1
        while i < h:
            for j in range(n):
                if haystack[i - j] != needle[-j - 1]:
                    i += skip.get(haystack[i], n)
                    break
            else:
                return i - n + 1
        return -1

    def similarity(self, focus1: str, focus2: str, context1: str = "", context2: str = ""):
        ''' Calculate cosine similarity between two phrases (focus1 and focus2).
            Both phrases can be accompanied by the context they were used to
            create more meaningful embeddings.'''
        if len(context1) == 0:
            context1 = focus1
        if len(context2) == 0:
            context2 = context1 + ", how about " + focus2 + "?"

        v1 = self.vectorize(focus1, context1)
        v2 = self.vectorize(focus2, context2)
        return self.cos(v1, v2)

    def most_similar(self, focus: str, context: str, possibilities: List[str]):
        ''' Find the most similar phrase to focus considering all possibilities '''
        v1 = self.vectorize(focus, context)
        max_similarity = 0.0
        top_elem = None

        for possibility in possibilities:
            v = self.vectorize(possibility, context + ', how about ' + possibility + "?")
            similarity = self.cos(v1, v)[0]
            if similarity > max_similarity:
                max_similarity = similarity
                top_elem = possibility

        return (top_elem, max_similarity)

    def rank_similarities(self, focus: str, context: str, possibilities: List[str], threshold=0.5):
        v1 = self.vectorize(focus, context)
        similarities = []

        for possibility in possibilities:
            v = self.vectorize(possibility, context + ', how about ' + possibility + "?")
            similarity = self.cos(v1, v)[0]
            similarities.append((possibility, similarity))
        return sorted(similarities, key=lambda x: x[1], reverse=True)
