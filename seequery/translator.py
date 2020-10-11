import logging
from typing import List, Optional, Tuple, Union

import spacy
import yaml
from spacy.cli.download import download as spacy_download

from seequery.embeddings.embeddings_manager import EmbeddingsManager
from seequery.ontology.ontology_manager import OntologyManager
from seequery.pipeline.pipeline import Pipeline


class CQToSPARQLOWL:
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)

        if not self.config:
            print(f"Cannot load config {config_path}, exiting...")
            exit(1)

        self.spacy_nlp = self._load_spacy(self.config['spacy_model'])
        self.embeddings_mngr = EmbeddingsManager(self.config['embeddings'],
                                                 self.spacy_nlp)
        self.ontology_mngr = OntologyManager(self.config['ontology'])
        self.pipeline = Pipeline(self.config['pipeline'],
                                 self.embeddings_mngr,
                                 self.ontology_mngr,
                                 self.spacy_nlp)

    def translate(self, cq: str,
                  dump_debug_info: bool = False) -> Union[List[str], List[Tuple[List[str], dict]]]:
        """Translate CQ into SPARQL-OWL query.

            Args:
                cq (str): Competency Question as string

            Returns:
                sparql-owl queries (List[str]): SPARQL-OWL query recommendations OR single-item list wih error
                                                OR a single-item list with tuple
                                                (recommendations, debug_state)
        """
        logging.debug(f'\n\nTranslating CQ: {cq}')

        output = self.pipeline.run(cq)

        if 'QueryGenerationFailure' in output:
            return [output['QueryGenerationFailure']]
        else:
            return output['queries'] if not dump_debug_info else [(output['queries'], output)]

    def _load_config(self, path: str) -> Optional[dict]:
        """Load application config YAML file.
            Args:
                path (str): path to config YAML file

            Returns:
                config (Optional[dict]): config dictionary or None
        """
        with open(path, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError:
                return None

    def _load_spacy(self, model_name: str) -> spacy.lang.xx.Language:
        """If a model name is available, load it, if not, download and load.
            Args:
                model_name (str): name of the model to be loaded.

            Returns:
                spacy model
        """
        try:
            model = spacy.load(model_name)
        except OSError:
            logging.debug(
                f"Model '{model_name}' not found. Downloading and installing.")
            spacy_download(model_name)
            model = spacy.load(model_name)

        return model
