import logging
import sys

from seequery.translator import CQToSPARQLOWL

logging.basicConfig(filename='cq_to_sparql.log', level=logging.DEBUG)

cqs = [
    'Are anchovies and capers used together?',
    'Are different bases available?',
    'Are there any children pizzas?',
    'Are toppings organic?',
    'Are we including the folded pizzas in our domain?',
    'Can I have a menu without pizzas please?',
    'Can I remove toppings from a pizza?',
    'Can you have a pizza with any combination of toppings?',
    'Do pizzas come in different sizes?',
    'Does a spicy pizza contain halal meat?',
    'What origins of pizza toppings are there?',
    'How many kinds of pizza I would make from 3 ingredients?',
    'How many pizzas are available?',
    'How many pizzas contain meat?',
    'How many pizzas did I eat last week?',
    'How many pizzas have either ham or chicken topping?',
    'How much does Margherita Pizza weight?',
    'How much it will cost me to order all pizzas in the menu?',
    'Is pizza healthy?',
    'Is spicy pizza stuffed crust and what is it stuffed with?',
    'Is spicy pizza thin or thick bread?',
    'Is vegetarian pizza deep pan or Chicago style?',
    'Should we include the oven type in the pizza definition?',
    'What are the types of pizza base options?',
    'What are the types of vegetarian pizza?',
    'What is the most popular topping?',
    'What is the third least popular topping?',
    'What kinds of pizza bases are possible?',
    'What kind of pizza contains a single meat ingredient?',
    'What pizzas contain less than 3 toppings?',
    'What sauces are available?',
    'Which are the gluten free bases?',
    'Which are the nut free pizzas?',
    'Which are the offers of the day?',
    'Which is the latest combination of toppings?',
    'Which pizzas are sharing 3 or more ingredients?',
    'Which pizzas are spicy?',
    'Which pizzas contain olives and peppers?',
    'Which pizzas contain prawns but not anchovy?',
    'Which pizzas do not have nuts?',
    'Which sort of cheese do we have?',
    'Which toppings are allowed for customization purposes?',
]

def main() -> None:
    if len(sys.argv) == 1:
        translator = CQToSPARQLOWL()
    else:
        config = CQToSPARQLOWL.load_config(sys.argv[1])
        translator = CQToSPARQLOWL(config=config)

    for cq in cqs:
        print(f"Processing CQ {cq}")
        query = translator.translate(cq)
        print(query)
        #print(translator.translate(input("Please type your CQ: "), dump_debug_info=True))
        #    print(query)
        #print("-" * 80)


if __name__ == '__main__':
    main()
