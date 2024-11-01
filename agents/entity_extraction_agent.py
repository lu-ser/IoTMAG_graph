from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import logging
import re
import os
import yaml

from agents.base_agent import LangChainAgent
from agents.EdgeWeightManager import EdgeWeightManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Entity:
    name: str
    type: str
    attributes: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __hash__(self):
        return hash((self.name, self.type))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return NotImplemented
        return self.name == other.name and self.type == other.type


@dataclass(frozen=True)
class Relation:
    source: str
    target: str
    type: str
    weight: float = 1.0
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), hash=True
    )

    @staticmethod
    def create(
        source: str,
        target: str,
        type_: str,
        weight: float = 1.0,
        timestamp: Optional[datetime] = None,
    ) -> "Relation":
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        elif isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            raise ValueError(f"Invalid timestamp type: {type(timestamp)}")

        return Relation(
            source=source, target=target, type=type_, weight=weight, timestamp=timestamp
        )


class EntityExtractionAgent(LangChainAgent):
    def __init__(self):
        self.prompts = self._load_prompts()
        super().__init__(provider="groq", system=self.prompts["extraction_prompt"])

        self.entities: Dict[str, Entity] = {}
        self.relations: Set[Relation] = set()
        self.edge_weights = EdgeWeightManager()

        self.enrichment_agent = LangChainAgent(
            provider="groq", system=self.prompts["enrichment_prompt"]
        )

    def _load_prompts(self) -> Dict[str, str]:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompts_path = os.path.join(project_root, "config", "prompts.yaml")
        with open(prompts_path, "r") as f:
            return yaml.safe_load(f)

    def _parse_response(
        self, response: str, timestamp: datetime
    ) -> Tuple[List[Entity], List[Relation]]:
        if "ENTITIES:" not in response:
            logger.warning("No ENTITIES section found in response")
            return [], []

        parts = response.split("ENTITIES:")
        entities_section = (
            parts[1].split("RELATIONS:")[0] if "RELATIONS:" in response else parts[1]
        )
        relations_section = (
            response.split("RELATIONS:")[1] if "RELATIONS:" in response else ""
        )

        # Parse entities
        entities = []
        current_entity = {}
        in_attributes = False

        for line in entities_section.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("- name:"):
                if current_entity:
                    entities.append(Entity(**current_entity, timestamp=timestamp))
                current_entity = {"attributes": {}}
                current_entity["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("type:"):
                current_entity["type"] = line.split(":", 1)[1].strip()
            elif line.startswith("attributes:"):
                in_attributes = True
            elif in_attributes and ":" in line:
                key, value = [x.strip() for x in line.split(":", 1)]
                current_entity["attributes"][key] = value

        if current_entity:
            entities.append(Entity(**current_entity, timestamp=timestamp))

        # Parse relations
        relations = []
        current_relation = {}

        if relations_section:
            for line in relations_section.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue

                if line.startswith("- source:"):
                    if current_relation:
                        relations.append(
                            Relation.create(
                                source=current_relation["source"],
                                target=current_relation["target"],
                                type_=current_relation["type"],
                                weight=current_relation.get("weight", 1.0),
                                timestamp=timestamp,
                            )
                        )
                    current_relation = {}
                    current_relation["source"] = line.split(":", 1)[1].strip()
                elif line.startswith("target:"):
                    current_relation["target"] = line.split(":", 1)[1].strip()
                elif line.startswith("type:"):
                    current_relation["type"] = line.split(":", 1)[1].strip()
                elif line.startswith("weight:"):
                    weight_str = line.split(":", 1)[1].strip()
                    weight_match = re.search(r"(\d*\.?\d+)", weight_str)
                    current_relation["weight"] = (
                        float(weight_match.group(1)) if weight_match else 1.0
                    )

            if current_relation:
                relations.append(
                    Relation.create(
                        source=current_relation["source"],
                        target=current_relation["target"],
                        type_=current_relation["type"],
                        weight=current_relation.get("weight", 1.0),
                        timestamp=timestamp,
                    )
                )

        return entities, relations

    def _is_significant_entity(self, entity: Entity) -> bool:
        common_terms = {
            "he",
            "she",
            "they",
            "it",
            "someone",
            "everyone",
            "anybody",
            "nobody",
        }

        if entity.name.lower() in common_terms:
            return False

        if len(entity.name) < 2 or not any(c.isalnum() for c in entity.name):
            return False

        confidence = entity.attributes.get("confidence")
        if confidence:
            confidence_match = re.search(r"(\d*\.?\d+)", str(confidence))
            if not confidence_match or float(confidence_match.group(1)) < 0.7:
                return False

        if not entity.attributes.get("significance"):
            return False

        return True

    def _enrich_entity(
        self, entity: Entity, timestamp: datetime
    ) -> Optional[Tuple[List[Entity], Set[Relation]]]:
        enrichment_prompt = self.prompts["enrichment_prompt"].format(
            entity_name=entity.name,
            entity_type=entity.type,
            current_context=entity.attributes.get("significance", ""),
        )

        self.enrichment_agent.add_message(enrichment_prompt)
        response = self.enrichment_agent.get_response()

        if "additional_entities:" not in response:
            return None

        parts = response.split("additional_entities:")
        entities_section = (
            parts[1].split("additional_relations:")[0]
            if "additional_relations:" in response
            else parts[1]
        )
        relations_section = (
            response.split("additional_relations:")[1]
            if "additional_relations:" in response
            else ""
        )

        return self._parse_response(
            f"ENTITIES:{entities_section}\nRELATIONS:{relations_section}", timestamp
        )

    def process_message(
        self, message: str, timestamp: Optional[datetime] = None
    ) -> Tuple[List[Entity], List[Relation]]:
        timestamp = self._normalize_timestamp(timestamp)

        sender, content = self._parse_message(message)
        if sender == "Unknown":
            logger.warning("Skipping message with unknown sender")
            return [], []

        analysis_prompt = self._create_analysis_prompt(sender, content)
        self.add_message(analysis_prompt)
        response = self.get_response()

        initial_entities, initial_relations = self._parse_response(response, timestamp)
        filtered_entities = [
            entity for entity in initial_entities if self._is_significant_entity(entity)
        ]

        sender_entity = Entity(
            name=sender,
            type="person",
            attributes={"first_seen": timestamp.isoformat()},
            timestamp=timestamp,
        )
        self.entities[sender] = sender_entity

        enriched_entities = []
        enriched_relations = set()

        for entity in filtered_entities:
            if entity.name != sender:
                enrichment_result = self._enrich_entity(entity, timestamp)
                if enrichment_result:
                    new_entities, new_relations = enrichment_result
                    enriched_entities.extend(new_entities)
                    enriched_relations.update(new_relations)

        all_entities = [sender_entity] + filtered_entities + enriched_entities
        all_relations = set(initial_relations).union(enriched_relations)

        self._update_state(all_entities, all_relations, timestamp)

        return all_entities, list(all_relations)

    def _normalize_timestamp(self, timestamp: Optional[datetime]) -> datetime:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp

    def _parse_message(self, message: str) -> Tuple[str, str]:
        message = message.strip()
        match = re.match(r"([^:]+):\s*(.*)", message)
        return (
            (match.group(1).strip(), match.group(2).strip())
            if match
            else ("Unknown", message.strip())
        )

    def _create_analysis_prompt(self, sender: str, content: str) -> str:
        return f"""Analyze this message from {sender}:
        "{content}"
        
        Focus on understanding {sender}'s relationship with the topics, skills, and concepts mentioned.
        Consider both explicit statements and implicit information about {sender}'s knowledge, interests, and expertise.
        
        Extract ALL possible meaningful entities and relationships, focusing on:
        1. Every distinct named person, organization, or place
        2. Every specific skill or expertise area mentioned
        3. Every tool, product, or technology referenced
        4. Every concrete project or initiative discussed
        5. Any clear interests or specializations revealed"""

    def _update_state(
        self, entities: List[Entity], relations: Set[Relation], timestamp: datetime
    ) -> None:
        for entity in entities:
            self.entities[entity.name] = entity

        for relation in relations:
            if relation.source in self.entities and relation.target in self.entities:
                self.relations.add(relation)
                self.edge_weights.add_mention(
                    relation.source, relation.target, relation.type, timestamp
                )

    def get_graph_data(self, time_filter: str = "now") -> Dict:
        cutoff_time = self._get_cutoff_time(time_filter)

        filtered_entities = {
            name: entity
            for name, entity in self.entities.items()
            if entity.timestamp >= cutoff_time
        }

        weighted_edges = self.edge_weights.get_all_edge_weights(
            datetime.now(timezone.utc)
        )

        nodes = [
            {
                "id": entity.name,
                "name": entity.name,
                "type": entity.type,
                "attributes": entity.attributes,
                "timestamp": entity.timestamp.isoformat(),
            }
            for entity in filtered_entities.values()
        ]

        edges = [
            {
                "source": edge["source"],
                "target": edge["target"],
                "type": edge["type"],
                "weight": edge["weight"],
            }
            for edge in weighted_edges
            if edge["source"] in filtered_entities
            and edge["target"] in filtered_entities
        ]

        return {"nodes": nodes, "edges": edges}

    def _get_cutoff_time(self, time_filter: str) -> datetime:
        now = datetime.now(timezone.utc)
        return now - {
            "now": timedelta(seconds=1),
            "1h": timedelta(hours=1),
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1),
            "1m": timedelta(days=30),
        }.get(time_filter, timedelta(0))

    def reset(self) -> None:
        self.entities.clear()
        self.relations.clear()
        self.edge_weights = EdgeWeightManager()
