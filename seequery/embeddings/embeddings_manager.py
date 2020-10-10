import numpy as np
import os
import pickle
from typing import Dict
from scipy import spatial
import logging
import spacy


class EmbeddingsManager:
    """ Manage predefined embeddings. """
    def __init__(self, emb_config: dict, spacy_nlp: spacy.lang.xx.Language) -> None:
        """ Load embeddings and provide methods to operate over them.

        Args:
            emb_config (dict): embedding manager config dict
        """
        self.spacy_nlp = spacy_nlp
        self.embeddings = self._load_embeddings(emb_config['emb_path'])
        self.emb_length = self._get_embedding_length()
        # self.equal_on_single_token = emb_config['equal_on_single_token']
        self.lemmatize = emb_config['lemmatize']

        # pickle embeddings if needed to speedup next runs
        if(not emb_config['emb_path'].endswith('.pickle') and
           not os.path.exists(f'{emb_config["emb_path"]}.pickle') and
           emb_config['pickle_it']):
            self.save(f'{emb_config["emb_path"]}.pickle')

    def phrase_similarity(self, phrase1: str, phrase2: str) -> float:
        """ Calculates similarity of two phrases (lowercased, space separated)

        Args:
            phrase1 (str): first phrase
            phrase2 (str): second phrase

        Returns:
            similarity (float): cosine similarity between phrases mass centers.
        """

        if self.lemmatize:
            phrase1 = " ".join([t.lemma_ for t in self.spacy_nlp(phrase1)])
            phrase2 = " ".join([t.lemma_ for t in self.spacy_nlp(phrase2)])
            logging.debug(f"Emb::lemmatization: {phrase1}, {phrase2}")

        if phrase1.lower() == phrase2.lower():
            return 1.0

        # If token not in embeddings, add random vector:
        for phrase in [phrase1, phrase2]:
            for token in phrase.split(" "):
                if token not in self.embeddings:
                    self.embeddings[token] = np.random.rand(self.emb_length)

        # else, get cosine similarity between centers of token vectors masses
        phrase1_center = np.mean(
            [self.embeddings[k] if k in self.embeddings else
             np.random.rand(self.emb_length) for k in phrase1.split(" ")],
            axis=0
        )
        phrase2_center = np.mean(
            [self.embeddings[k] if k in self.embeddings else
             np.random.rand(self.emb_length) for k in phrase2.split(" ")],
            axis=0
        )
        return 1. - spatial.distance.cosine(phrase1_center, phrase2_center)

    def _load_embeddings(self, path: str) -> Dict[str, np.array]:
        """ Load GloVe embeddings from given file.

        Args:
            path (str): path with GloVe embeddings

        Returns:
            Dict[str, np.array]: dict mapping tokens into vectors
        """
        token_to_embedding = {}
        if path.endswith(".pickle"):
            pickled_path = path
        else:
            pickled_path = path + ".pickle"

        if os.path.exists(pickled_path):
            return pickle.load(open(pickled_path, 'rb'))
        else:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if len(line) == 0:
                        continue
                    word, *embedding = line.split(" ")
                    token_to_embedding[word] = \
                        np.array(embedding).astype(np.float)
            return token_to_embedding

    def _get_embedding_length(self) -> int:
        """ Calculate the size of embeddings provided

        Returns:
            length (int): length of the embedding
        """
        if len(self.embeddings) == 0:
            return 0
        for token, vec in self.embeddings.items():
            return vec.size
        return 0

    def save(self, path: str) -> None:
        """ Save pickled embeddings for quicker processing

        Args:
            path (str): path to save pickles, will auto add .pickle ext

        """
        with open(path, 'wb') as handle:
            pickle.dump(self.embeddings, handle, protocol=pickle.HIGHEST_PROTOCOL)
