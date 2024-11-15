from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from agents.base_agent import LangChainAgent
import logging
from datetime import datetime, timedelta, timezone
import re

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Helper function to get current UTC time."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Entity:
    name: str
    type: str
    attributes: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=get_utc_now)

    def __hash__(self):
        return hash((self.name, self.type))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return NotImplemented
        return self.name == other.name and self.type == other.type


@dataclass
class Relation:
    source: str
    target: str
    type: str
    weight: float = 1.0
    timestamp: datetime = field(default_factory=get_utc_now)


class EntityExtractionAgent(LangChainAgent):
    def __init__(self):
        system_prompt = """You are an expert at analyzing conversations and extracting a person-centered knowledge graph. Your goal is to build a rich network of information around the person sending the message, including their interests, skills, knowledge, and connections.

        Follow these rules:
        1. Person Analysis (central focus):
           When a person sends a message like "Luigi: Hello everyone", treat "Luigi" as the central node.
           For the person, identify:
           - status: their current state or situation
           - experience_level: overall expertise level
           - primary_interests: main areas of interest
           - role: their professional or social role if mentioned
           
        2. Topic Identification (in relation to the person):
           For each topic mentioned or implied, identify:
           - category: main category (technology, science, art, business, etc.)
           - relevance: how relevant to the person (high, medium, low)
           - person_expertise: person's level in this topic (beginner, intermediate, expert)
           - mentioned_context: how it came up in conversation
           - impact: how it affects or interests the person
           
        3. Skills and Knowledge (person-specific):
           For each skill or knowledge area:
           - proficiency: person's level (beginner, intermediate, expert)
           - usage: how they use or apply it
           - learning_status: currently learning, actively using, teaching others
           - interests: their interest level in developing this skill
           
        4. Person-Centric Relationships:
           Create meaningful connections showing how the person relates to each entity:
           - person -> topic (knows: 0.8, interested_in: 0.6, expert_in: 0.9)
           - person -> skill (learning: 0.4, practicing: 0.7, mastered: 0.9)
           - person -> tool (uses: 0.8, familiar_with: 0.6, prefers: 0.9)
           - person -> concept (understands: 0.7, developing: 0.5, teaches: 0.9)
           
        5. Entity Interconnections (through the person's perspective):
           Show how entities connect through the person:
           - topic -> topic (person_sees_connection: 0.7, person_applies_together: 0.8)
           - skill -> tool (person_uses_for: 0.8, person_learning_with: 0.6)
           - concept -> topic (person_understands_relation: 0.7)
        6. Filtering Out Irrelevant Content: Avoid superficial or non-significant content, such as:
            Greetings or polite expressions ("hello", "good morning")
            Personal pronouns ("I", "he", "we"), unless essential for context
            Generic, vague phrases lacking specific details or relevance to the analysis
            Examples to exclude:
            "Hello everyone!"
            "I agree with this."
            "I think it can be done."
           
        Output must be in this exact format:
        ENTITIES:
        - name: entity_name
          type: entity_type
          attributes:
            key1: value1
            key2: value2

        RELATIONS:
        - source: entity_name
          target: entity_name
          type: relationship_type
          weight: 0.8
          THE TYPE SHOULD WITHIN THE FOLLOWING GROUP: person, interest, activity, skill, tool, concept, organization
        """

        super().__init__(provider="groq", system=system_prompt)
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []

    def process_message(
        self, message: str, timestamp: Optional[datetime] = None
    ) -> Tuple[List[Entity], List[Relation]]:
        """Process a message and extract entities and relations, focusing on the sender."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        elif timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        try:
            # Extract sender and message content
            sender, content = self._parse_message(message)

            # Create the analysis prompt
            analysis_prompt = f"""Analyze this message from {sender}:
            "{content}"
            
            Focus on understanding {sender}'s relationship with the topics, skills, and concepts mentioned.
            Consider both explicit statements and implicit information about {sender}'s knowledge, interests, and expertise.
            
            Think carefully about:
            1. What this reveals about {sender}'s interests and knowledge
            2. How {sender} relates to the topics mentioned
            3. What skills or expertise {sender} demonstrates
            4. How different topics or concepts connect through {sender}'s perspective

            Remember to use the exact YAML format specified."""

            self.add_message(analysis_prompt)
            response = self.get_response()
            new_entities, new_relations = self._parse_response(response, timestamp)

            # Ensure the sender exists as an entity
            sender_entity = Entity(
                name=sender,
                type="person",
                attributes={"first_seen": timestamp.isoformat()},
                timestamp=timestamp,
            )
            self.entities[sender] = sender_entity

            # Update internal state
            for entity in new_entities:
                self.entities[entity.name] = entity

            # Filter valid relations and add them
            valid_relations = []
            for relation in new_relations:
                if (
                    relation.source in self.entities
                    and relation.target in self.entities
                ):
                    valid_relations.append(relation)

            self.relations.extend(valid_relations)
            return new_entities, valid_relations

        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            logging.error(f"Message: {message}")
            logging.error(f"Timestamp: {timestamp}")
            raise e

    def _parse_message(self, message: str) -> Tuple[str, str]:
        """Extract sender and content from a message."""
        # Try to match the pattern "Sender: Message"
        match = re.match(r"^([^:]+):\s*(.*)$", message.strip())
        if match:
            return match.group(1).strip(), match.group(2).strip()
        else:
            # If no sender is specified, use "Unknown"
            logging.warning("No sender specified in message, using 'Unknown'")
            return "Unknown", message.strip()

    def _parse_response(
        self, response: str, timestamp: datetime
    ) -> Tuple[List[Entity], List[Relation]]:
        """Parse the YAML response into Entity and Relation objects with the specified timestamp."""
        try:
            # Split response into entities and relations sections
            if "ENTITIES:" not in response:
                logging.warning("No ENTITIES section found in response")
                return [], []

            parts = response.split("ENTITIES:")
            entities_section = (
                parts[1].split("RELATIONS:")[0]
                if "RELATIONS:" in response
                else parts[1]
            )
            relations_section = (
                response.split("RELATIONS:")[1] if "RELATIONS:" in response else ""
            )

            # Parse entities with explicit timestamp
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
                    in_attributes = False
                elif line.startswith("type:"):
                    current_entity["type"] = line.split(":", 1)[1].strip()
                elif line.startswith("attributes:"):
                    in_attributes = True
                elif in_attributes and ":" in line:
                    key, value = [x.strip() for x in line.split(":", 1)]
                    current_entity["attributes"][key] = value

            if current_entity:
                entities.append(Entity(**current_entity, timestamp=timestamp))

            # Parse relations with explicit timestamp
            relations = []
            if relations_section:
                current_relation = {}
                for line in relations_section.strip().split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("- source:"):
                        if current_relation:
                            relations.append(
                                Relation(**current_relation, timestamp=timestamp)
                            )
                        current_relation = {}
                        current_relation["source"] = line.split(":", 1)[1].strip()
                    elif line.startswith("target:"):
                        current_relation["target"] = line.split(":", 1)[1].strip()
                    elif line.startswith("type:"):
                        current_relation["type"] = line.split(":", 1)[1].strip()
                    elif line.startswith("weight:"):
                        try:
                            current_relation["weight"] = float(
                                line.split(":", 1)[1].strip()
                            )
                        except ValueError:
                            current_relation["weight"] = 1.0

                if current_relation:
                    relations.append(Relation(**current_relation, timestamp=timestamp))

            logging.info(
                f"Parsed {len(entities)} entities and {len(relations)} relations"
            )
            return entities, relations

        except Exception as e:
            logging.error(f"Error parsing response: {e}")
            logging.error(f"Response was:\n{response}")
            return [], []

    def get_graph_data(self, time_filter: str = "now") -> Dict:
        """Return the current graph state filtered by time."""
        cutoff_time = self._get_cutoff_time(time_filter)

        logging.debug(f"Filtering graph data with time_filter: {time_filter}")
        logging.debug(f"Cutoff time: {cutoff_time}")

        # Filter entities and relations by timestamp
        filtered_entities = {}
        for name, entity in self.entities.items():
            logging.debug(f"Entity {name} timestamp: {entity.timestamp}")
            if entity.timestamp >= cutoff_time:
                filtered_entities[name] = entity
                logging.debug(f"Including entity {name}")
            else:
                logging.debug(f"Excluding entity {name} (too old)")

        filtered_relations = []
        for relation in self.relations:
            logging.debug(
                f"Relation {relation.source}->{relation.target} timestamp: {relation.timestamp}"
            )
            if relation.timestamp >= cutoff_time:
                filtered_relations.append(relation)
                logging.debug(
                    f"Including relation {relation.source}->{relation.target}"
                )
            else:
                logging.debug(
                    f"Excluding relation {relation.source}->{relation.target} (too old)"
                )

        # Only include nodes that have valid connections
        used_entities = set()
        for relation in filtered_relations:
            if (
                relation.source in filtered_entities
                and relation.target in filtered_entities
            ):
                used_entities.add(relation.source)
                used_entities.add(relation.target)

        nodes = [
            {
                "id": e.name,
                "name": e.name,
                "type": e.type,
                "attributes": e.attributes,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in filtered_entities.values()
            if e.name in used_entities
        ]

        edges = [
            {
                "source": r.source,
                "target": r.target,
                "type": r.type,
                "weight": r.weight,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in filtered_relations
            if r.source in used_entities and r.target in used_entities
        ]

        logging.info(f"Returning {len(nodes)} nodes and {len(edges)} edges")
        return {
            "nodes": nodes,
            "edges": edges,
        }

    def reset(self):
        """Reset the agent's state."""
        self.entities = {}
        self.relations = []
        logger.info("Agent state reset")

    def _get_cutoff_time(self, time_filter: str) -> datetime:
        """Calculate cutoff time based on filter."""
        now = datetime.now(timezone.utc)
        if time_filter == "now":
            return now - timedelta(seconds=1)  # Include very recent messages
        elif time_filter == "1h":
            return now - timedelta(hours=1)
        elif time_filter == "1d":
            return now - timedelta(days=1)
        elif time_filter == "1w":
            return now - timedelta(weeks=1)
        elif time_filter == "1m":
            return now - timedelta(days=30)
        else:
            return datetime.min.replace(tzinfo=timezone.utc)
