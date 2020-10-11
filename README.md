# SeeQuery
CQ to SPARQL-OWL translation recommender

A tool helping ontology engineers to keep track of the quality of their ontologies.
It can be used during the ontology authoring process involving competency questions (CQs), being questions which the ontology should be able to answer to. To access knowledge modelled in the ontology, `SeeQuery` tranlates each CQ into `SPARQL-OWL` queries.

## How to use it?
- Ensure you have `Python3` installed (recommended `Python version 3.8`)
- Install all dependencies: `pip install -r requirements.txt`
- Open `config.yaml` and choose a path to your ontology (ontology which should be queried) in `onto_id` field
- Download and set a proper path to your embeddings. We recommend to use `glove.840B.300d` model available on https://nlp.stanford.edu/projects/glove/. If you store your embeddings in `resources/embeddings/glove.840B.300d.txt` you should leave the default embedding path in the config file as is.
- Change default parameters if needed.
- Run `PYTHONPATH=. python seequery.translation_loop.py`

*WARNING:* Utilizing pretrained, static word embedding makes `SeeQuery` a resource-heavy tool. Ensure you have about *10GB of free space* on your disk.

After all resources are loaded, you will see a prompt encouraging you to type your CQs. Each CQ typed results with a list of `SPARQL-OWL` recommendations if it is possible to construct a query or a status code telling that it is impossible to construct a query.

## Are there any predefined examples of usage?
Sure, we have evaluated the method on two ontologies: Pizza and TrhOnto. Both ontologies are uploaded in the `resources/ontologies/` folders. For evaluation purposes, we collected a set of predefined CQs. They can be seen in `seequery/evaluate_pizza.py` and `seequery/evaluate_trh.py` files. To run evaluations and reproduce our scores -- run:
- `PYTHONPATH=. python seequery/evaluate_pizza.py` -- ensure that `config.yaml` has `pizza` set as the value of `onto_id`!
- `PYTHONPATH=. python seequery/evaluate_trh.py` -- ensure that `config.yaml` has `trh` set as the value of `onto_id`!

## How well does it work?
The overall quality of the method is estimated on Pizza (59.46% output scores are classified as correct) and TRHOnto (50% classified as correct) and is limited mostly due missing SPARQL-OWL templates. Having a bigger/more various resource than CQ2SPARQLOWL as the source of CQ to SPARQL-OWL, the coverage of SPARQL-OWL templates could be higher resulting in higher scores.
We provide an in-detail evaluation reports in `evaluation_resources` folder (for `pizza` and `trhonto` separately).

## What are the other ontologies provided?
`SeeQuery` is a general framework for translating CQs into queries. However, in order to run it it requires mappings from some dataset of CQ to SPARQL-OWL examples, since the method is template based. To construct our mappings (you can find them in `resources/cq_to_query/pattern_mapping.json`) we utilized `CQ2SPARQLOWL` (https://github.com/CQ2SPARQLOWL/Dataset) the biggest to date dataset of CQ to SPARQL-OWL examples. We also used `CQ2SPARQLOWL` to fine-tune our hyperparameters. For this purpose, we needed to use ontologies provided in the dataset and you can find them in `resources/ontologies` as well as `pizza` and `trhonto` -- our evaluation ontologies.
