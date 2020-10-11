import re
from dataclasses import dataclass, field
from typing import Set


@dataclass
class MetaTemplateChunks:
    '''Class for keeping track of a match'''
    chunks: Set[str] = field(default_factory=set)
    ecs_used_as_pcs: Set[str] = field(default_factory=set)
    data_property_chunks: Set[str] = field(default_factory=set)
    object_property_chunks: Set[str] = field(default_factory=set)
    relations: Set[str] = field(default_factory=set)
    entities: Set[str] = field(default_factory=set)

    @staticmethod
    def from_template(template: str) -> 'MetaTemplateChunks':
        """ Construct meta information from a template itself.

        Args:
            template (str): template to construct from
        Returns:
            MetaTemplateChunks: meta information extracted
        """
        template_lowercased = template.lower()
        ecs_used_as_pcs = set()
        object_property_chunks = set()
        data_property_chunks = set()
        chunks_in_template = set()

        for bracket_chunk in re.finditer("<(IS_EC|HAS_EC|EC|PC)[0-9]+>", template):
            chunk = bracket_chunk.group()[1:-1]  # strip angle brackets
            bracket_end_pos = bracket_chunk.span()[1]

            if "_" in chunk:
                chunk = chunk.split(" ")[1]
                ecs_used_as_pcs.add(chunk)

            if chunk in ecs_used_as_pcs or chunk.startswith("PC"):
                if "somevaluesfrom" in template_lowercased[bracket_end_pos:bracket_end_pos + 30]:
                    object_property_chunks.add(chunk)
                elif "hasvalue" in template_lowercased[bracket_end_pos:bracket_end_pos + 30]:
                    data_property_chunks.add(chunk)

            chunks_in_template.add(chunk)
            relations = ecs_used_as_pcs | object_property_chunks | data_property_chunks
            entities = chunks_in_template - relations

        return MetaTemplateChunks(chunks=chunks_in_template,
                                  ecs_used_as_pcs=ecs_used_as_pcs,
                                  data_property_chunks=data_property_chunks,
                                  object_property_chunks=object_property_chunks,
                                  relations=relations, entities=entities)

    def can_be_handled(self) -> bool:
        """ Check if template can be handled with SpaCy.

        Returns:
            bool: True if at most one PC and at most 2 ECs
        """
        properties = self.ecs_used_as_pcs | self.object_property_chunks | self.data_property_chunks
        entities = self.chunks - properties

        if len(properties) <= 1 and (len(entities) > 0 and len(entities) < 3):
            return True
        else:
            return False
