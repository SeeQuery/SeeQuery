import logging
import sys
from seequery.translator import CQToSPARQLOWL


logging.basicConfig(filename='cq_to_sparql.log', level=logging.DEBUG)

cqs = [
    "Which exercises are contraindicated for a patient?",
    "Which exercises are recommended for a patient?",
    "Which movements compose an exercise?",
    "Which are the body parts that compose a shoulder?",
    "Which is the type of an auxiliary movement?",
    "Which body part does an auxiliary movement refer to?",
    "Which range of movement does a movement cover?",
    "Which exercises compose a phrase of a treatment protocool?",
    ("Which are the conditions that a patient must fulfill in order to be "
     "in a phsase of a treatment protocol?"),
    "Which is the laterality of a shoulder?",
    "Which results are obtainedfrom the exploration of the joint movement of the patient?",
    "What is the physiotherapy diagnostics of the patient?",
    "Which is the family and personal past history of the patient?",
    "How much pain does the patient report on the Visual Analogue Scale (VAS)?",
    ("Which are the conditions that an exercise must fulfill to be a candidate exercise "
     "for a phase of a treatment protocol?"),
    "What is the patient's age?",
    "Which health issue does the patient report?",
    "Which are the patient's recovery goals?",
    "Which phase is a patient in?",
    "Which exercises do patients usually perform badly?"
]


def main() -> None:
    if len(sys.argv) == 1:
        translator = CQToSPARQLOWL()
    else:
        translator = CQToSPARQLOWL(config_path=sys.argv[1])

    for cq in cqs:
        print(f"Processing {cq}")
        for output in translator.translate(cq, dump_debug_info=True):
            print(f"\t{output}")
        print("-" * 80)


if __name__ == '__main__':
    main()
