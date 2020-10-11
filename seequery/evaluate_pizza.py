import logging
import sys

from seequery.translator import CQToSPARQLOWL

logging.basicConfig(filename='cq_to_sparql.log', level=logging.DEBUG)

cqs = [
    'What are the types of vegetarian pizza?',
    'What are the types of base options?',
    'Which are real italian pizzas?',
    'Are different bases avaialable?',
    'How many pizzas are available?',
    'How many pizzas contain meat?',
    'Which sort of cheese do we have?',
    'What sauces are available?',
    'What kind of pizza contains a single meat ingredient?',
    'Which are the nut free pizzas?',
    'Which pizzas are sharing 3 or more ingredients?',
    'Which pizzas do not have nuts?',
    'How many pizzas have either ham or chicken topping?',
    'Which pizzas contain prawns but not anchovy',
    'Which pizzas are spicy?',
    'Are anchovies and capers used together?',
    'Which pizzas contain peppers and olives?',
    'Can you have a pizza with any combination of toppings?',
    'What pizzas contain less than 3 toppings?',
    'What kind of pizza bases are possible?',
    'Do pizzas come in different sizes?',
    'Can I remove toppings from a pizza?',
    'Does this pizza contain halal meat?',
    'Are we including the folded pizzas in our domain?',
    'Is vegetarian pizza deep pan or Chicago style?',
    'What are the origins of pizza toppings?',
    'Is spicy pizza stuffed crust and what is it stuffed with?',
    'How much it will cost me to order all pizzas in the menu?',
    'Which toppings are allowed for customization purposes?',
    'Are toppings organic?',
    'Can I have a menu without pizzas please?',
    'Which are the offers of the day?',
    'Which is the latest combination of toppings?',
    'Are there any children pizzas?',
    'Is spicy pizza thin or thick bread?',
    'How much does Margherita Pizza weight?',
    'Is pizza healthy?'
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
