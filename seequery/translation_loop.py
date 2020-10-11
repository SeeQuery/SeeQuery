import logging
import sys

from seequery.translator import CQToSPARQLOWL

logging.basicConfig(filename='cq_to_sparql.log', level=logging.DEBUG)


def main() -> None:
    if len(sys.argv) == 1:
        translator = CQToSPARQLOWL()
    else:
        translator = CQToSPARQLOWL(config_path=sys.argv[1])

    while True:
        for query in translator.translate(input("Please type your CQ: ")):
            print(query)
        print("-" * 80)


if __name__ == '__main__':
    main()
