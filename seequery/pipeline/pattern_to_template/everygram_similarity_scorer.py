from nltk.util import everygrams
from nltk.tokenize import word_tokenize
from typing import List


class EverygramSimilarityScorer():
    """ Calculate Jaccard similarity over everygrams """
    def score(self, text1: str, text2: str) -> float:
        """
            Calculate Jaccard similarity over everygrams

            Args:
                text1 (str): text1 to be scored
                text2 (str): text2 to be scored

            Returns:
                float: jaccard score
        """
        set1 = set(self.get_everygrams(text1))
        set2 = set(self.get_everygrams(text2))
        return 1.0 * len(set1 & set2) / len(set1 | set2)

    def get_everygrams(self, text: str) -> List[List[str]]:
        """
            Generate everygrams from a given text

            Args:
                text (str): text to generate everygrams from

            Returns:
                List[List[str]]: everygrams generated
        """
        text = word_tokenize(text)
        return list(everygrams(text))
