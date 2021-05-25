import os
from typing import Any, Dict, List, Optional, Set, Tuple

import owlready2

from seequery.utils.helpers import Helpers
from seequery.utils.linking_category import LinkingCategory


class OntologyManager:
    """ Manage ontology. """
    def __init__(self, config: dict) -> None:
        """ Load ontology and provide methods to operate over it.

        Args:
            config (dict): config dict
        """
        self.ontology = self._load_ontology(config['onto_id'])
        self.onto_map = {
            LinkingCategory.CLASS: {self._get_label(c): c for c in
                                    self.ontology.classes()},
            LinkingCategory.DATA_PROPERTY: {self._get_label(p): p for p in
                                            self.ontology.data_properties()},
            LinkingCategory.OBJECT_PROPERTY: {self._get_label(p): p for p in
                                              self.ontology.object_properties()},
            LinkingCategory.INDIVIDUAL: {self._get_label(i): i for i in
                                         self.ontology.individuals()}
        }
        self.entities = [k for k, _ in self.onto_map[LinkingCategory.CLASS].items()] + [k for k, _ in self.onto_map[LinkingCategory.INDIVIDUAL].items()]
        self.properties = [k for k, _ in self.onto_map[LinkingCategory.OBJECT_PROPERTY].items()] + [k for k, _ in self.onto_map[LinkingCategory.DATA_PROPERTY].items()]
        self.prop_examples = self.get_usages()

    def calc_restriction_score(self, predicate: Any, obj1: Any,
                               obj2: Any = None) -> Tuple[float, Optional[bool]]:
        """
            Check if given predicate can be used with selected arguments
            also check if arguments have to be inversed in their order
            to match domain/range restrictions

            Args:
                predicate (Any): predicate to use
                obj1 (Any): predicate argument
                obj2 (Any): predicate argument

            Returns:
                Tuple[float, Optional[bool]]: restriction score with argswitch info
        """
        subject_with_ancestors = set(obj1.ancestors())
        subject_with_ancestors.add(obj1)

        if obj2:
            object_with_ancestors = set(obj2.ancestors())
            object_with_ancestors.add(obj2)
        else:
            object_with_ancestors = set()

        if len(predicate.domain) == 0 and len(predicate.range) == 0:
            # assign highest score when no restrictions
            return 1.0, None
        # empty domain -> check range only
        if len(predicate.domain) == 0:
            if len(set(predicate.range) & object_with_ancestors) > 0:
                return 1.0, False
            elif len(set(predicate.range) & subject_with_ancestors) > 0:
                return 1.0, True
            else:
                return 0.0, None

        # empty range -> check domain only
        elif len(predicate.range) == 0:
            if len(set(predicate.domain) & object_with_ancestors) > 0:
                return 1.0, True
            elif len(set(predicate.domain) & subject_with_ancestors) > 0:
                return 1.0, False
            else:
                return 0.0, None  # 0.5?

        # if in domain AND range
        elif(len(set(predicate.domain) & subject_with_ancestors) > 0 and
             len(set(predicate.range) & object_with_ancestors) > 0):
            return 1.0, False
        elif(len(set(predicate.range) & subject_with_ancestors) > 0 and
             len(set(predicate.domain) & object_with_ancestors) > 0):
            return 1.0, True  # inversed!
        else:
            return 0.0, None

    def calc_usage_score(self, predicate: Any, subject: Any, obj: Any = None) -> Tuple[float, Optional[bool]]:
        """
            Assign a score based on axioms presented in an ontology, if  object
            was seen with given predicate it should generate good score,
            if predicate is used with a subclass of given class
            it also should generate a good score.
            The function notices if arguments (subject, obj) of
            the predicate are inversed when they are used.

            Args:
                predicate (Any): predicate to use
                subject (Any): predicate subject
                object (Any): predicate object

            Returns:
                Tuple[float, Optional[bool]]: usage score, between 0 and 1 and (optional) argswitch
        """
        max_score = 0.0
        arg_switch = None

        # iterate over all predicate instanes (relations)
        if predicate not in self.prop_examples:
            return 0.0, None

        for subj_obj in self.prop_examples[predicate]:
            pred_subject, pred_object = subj_obj[0], subj_obj[1]
            # explicit usage
            if(pred_subject == subject and pred_object == obj):
                return 1.0, False
            elif pred_subject == obj and pred_object == subject:
                return 1.0, True  # argswitch!
            # one sided exact match and ancestor match
            elif (subject in self._get_ancestors(pred_subject) and
                  pred_object == obj):
                max_score, arg_switch = \
                    self._max_update(0.75, max_score, arg_switch, False)
            elif (obj and subject == pred_subject and
                  obj in self._get_ancestors(pred_object)):
                max_score, arg_switch = \
                    self._max_update(0.75, max_score, arg_switch, False)
            elif (subject in self._get_ancestors(pred_object) and
                  pred_object == subject):
                max_score, arg_switch = \
                    self._max_update(0.75, max_score, arg_switch, True)
            elif (obj and subject == pred_object and
                  subject in self._get_ancestors(pred_object)):
                max_score, arg_switch = \
                    self._max_update(0.75, max_score, arg_switch, True)
            # single sided explicit match
            elif (pred_subject == subject or pred_object == obj):
                max_score, arg_switch = \
                    self._max_update(0.5, max_score, arg_switch, False)
            elif (pred_object == subject or pred_subject == obj):
                max_score, arg_switch = \
                    self._max_update(0.5, max_score, arg_switch, True)
            # single sided ancestor match
            elif (subject in self._get_ancestors(pred_subject) or
                  obj in self._get_ancestors(pred_object)):
                max_score, arg_switch = \
                    self._max_update(0.25, max_score, arg_switch, False)
            elif (subject in self._get_ancestors(pred_object) or
                  obj in self._get_ancestors(pred_subject)):
                max_score, arg_switch = \
                    self._max_update(0.25, max_score, arg_switch, True)

        return max_score, arg_switch

    def _max_update(self, score: float, max_score: float, argswitch: Optional[bool],
                    new_argswitch: Optional[bool]) -> Tuple[float, Optional[bool]]:
        """ Update max_score and argswitch if current score is better than current max.

        Args:
            score (float): current score
            max_score (float): current max score
            argswitch (Optional[bool]): current should arguments be inverted
            new_argswitch (Optional[bool]): new should arguments be inverted

        Returns:
            Tuple[float, Optional[bool]]: max score and decision -- should args be switched?
        """
        if score > max_score:
            return score, new_argswitch
        else:
            return max_score, argswitch

    def _get_ancestors(self, obj: Any = None) -> Set[Any]:
        """ Return ancestors of a given object

        Returns:
            set: ancestors of a given object
        """
        if not obj:
            return set()
        else:
            return set(obj.ancestors())

    def _load_ontology(self, ontology_id: str) -> Any:
        """ Load ontology from its id or filepath

        Args:
            ontology_id (str): ontology id or filepath to load

        Returns:
            Any: ontology
        """
        if os.path.exists(ontology_id):
            path = ontology_id
        else:
            path = Helpers.onto2path(ontology_id)
        return owlready2.get_ontology(f"file://{path}").load()

    def _get_label(self, obj: Any) -> str:
        """ Return best label for given element.

        Args:
            obj (Any): object to get label from

        Returns:
            str: label of a given object
        """
        if hasattr(obj, 'prefLabel') and obj.prefLabel.first() is not None:
            label = obj.prefLabel.first()
        elif obj.label.first() is not None:
            label = obj.label.first()
        else:
            label = obj.name
        return Helpers.normalize_label(label)

    def get_usages(self) -> Dict[Any, List[Tuple[Any, Any]]]:
        """ Generate properties associated with a list of tuples with arguments used with it

        Returns:
            dict: properties associated with a list of tuples with arguments used with it
        """
        usages: dict = dict()

        for subject in self.ontology.classes():
            for prop in subject.get_class_properties():
                if prop not in usages:
                    usages[prop] = []

                for obj in prop[subject]:
                    if isinstance(obj, owlready2.entity.ThingClass):
                        usages[prop].append((subject, obj))
                    else:
                        usages[prop].append((subject, None))
        return usages
