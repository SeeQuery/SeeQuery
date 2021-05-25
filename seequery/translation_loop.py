import logging
import sys

from seequery.translator import CQToSPARQLOWL

logging.basicConfig(filename='cq_to_sparql.log', level=logging.DEBUG)


def main() -> None:
    if len(sys.argv) == 1:
        translator = CQToSPARQLOWL()
    else:
        config = CQToSPARQLOWL.load_config(sys.argv[1])
        translator = CQToSPARQLOWL(config=config)

    while True:
        print(translator.translate(input("Please type your CQ: "), dump_debug_info=True))
        #    print(query)
        print("-" * 80)


if __name__ == '__main__':
    main()
