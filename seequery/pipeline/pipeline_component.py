from abc import ABC, abstractmethod


class PipelineComponent(ABC):
    @abstractmethod
    def process(self, data: dict) -> dict:
        """
            A method processing given data with current pipeline step.

            Args:
                data (dict): a dict holding object state

            Returns:
                dict: a dict holding object state enriched with current pipeline results
        """
        pass
