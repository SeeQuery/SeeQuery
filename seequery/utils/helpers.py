import re
from typing import List, Tuple


class Helpers:
    @staticmethod
    def onto2path(ontology_name_or_path: str) -> str:
        """ Get path to ontology.

        Args:
            ontology_name_or_path (str): ontology name or path to it

        Returns:
            Path to ontology
        """
        prefix = "./resources/ontologies/"
        predefined_map = {
            "swo": f"{prefix}/swo_merged.owl",
            "awo": f"{prefix}/AfricanWildlifeOntology1.owl",
            "ontodt": f"{prefix}/OntoDT.owl",
            "stuff": f"{prefix}/stuff.owl",
            "demcare": f"{prefix}/exchangemodel.owl",
            "trh": f"{prefix}/trh.owl",
            "pizza": f"{prefix}/pizza.owl"
        }
        if ontology_name_or_path in predefined_map:
            return predefined_map[ontology_name_or_path]
        else:
            return ontology_name_or_path

    @staticmethod
    def normalize_label(label: str) -> str:
        """ Handle different naming conventions and transform them into common
            form.

        Args:
            label (str): label to be normalized

        Returns:
            normalized label
        """
        label = re.sub(r"['\"`]+", "", label)  # remove apostrophes
        label = re.sub(r"[-/\\ \t_]+", " ", label)  # normalize separators
        lower_count = sum(map(str.islower, label))
        upper_count = sum(map(str.isupper, label))
        if " " not in label and lower_count > 0 and upper_count > 0:
            # camel case to "normal case"
            label = re.sub("r([a-z])([A-Z])", r"\g<1> \g<2>", label)
        label = re.sub(r"(^[Tt]he |^[Aa] )", "", label)  # drop determiner
        return label.lower()

    @staticmethod
    def clean_cq(cq: str) -> str:
        """ Clean a CQ from unexpected characters.

        Args:
            cq (str): CQ to be cleaned

        Returns:
            cleaned CQ
        """
        normalizers = {
            r"[-\"\'”]": "",  # remove all dashes and quotations
            r"\(.*?\)": "",   # remove all ( )
            r"[ \t]+": " ",   # remove all multiplied whitespaces
            r" \?": "?"       # remove whitespaces before ?
        }

        for regex in normalizers:
            cq = re.sub(regex, normalizers[regex], cq)
        return cq

    @staticmethod
    def is_subspan(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        """ Check if one span is a subspan of the other one.

        Args:
            a (Tuple[int, int]): a pair of ints representing the first span
            b (Tuple[int, int]): a pair of ints representing the second span

        Returns:
            True if `a` is subspan of `b`, False otherwise.
        """
        if a[0] >= b[0] and a[1] <= b[1]:
            return True
        else:
            return False

    @staticmethod
    def span_overlap(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        """ Check if two spans overlap.

        Args:
            a (Tuple[int, int]): a pair of ints representing the first span
            b (Tuple[int, int]): a pair of ints representing the second span

        Returns:
            True if `a` overlaps `b`, False otherwise.
        """
        return not (a[0] > b[1] or a[1] < b[0])

    @staticmethod
    def filter_subspans(spans: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """ From a given list of spans, remove items being subspans of others.

        Args:
            spans (List[Tuple[int, int]]): list of spans

        Returns:
            Filtered list of spans.
        """
        filtered = []

        for span in spans:
            accept = True
            for compared in spans:
                if span[0] >= compared[0] and span[1] <= compared[1]:
                    if span[0] != compared[0] or span[1] != compared[1]:
                        accept = False
            if accept:
                filtered.append(span)

        filtered = list(dict.fromkeys(filtered))  # remove duplicates if present

        return filtered
