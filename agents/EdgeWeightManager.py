from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from agents.base_agent import LangChainAgent
import logging
from datetime import datetime, timedelta, timezone
import re
import math


@dataclass
class EdgeMentions:
    """Classe per tracciare le menzioni di un arco nel tempo"""

    source: str
    target: str
    type: str
    timestamps: List[datetime]
    base_weight: float = 0.3


class EdgeWeightManager:
    def __init__(self):
        self.decay_factors = {
            "hour": 0.05,  # Ridotto per un decadimento più lento
            "day": 0.15,
            "week": 0.35,
        }
        self.saturation_factor = 0.3  # Ridotto per una saturazione più graduale
        self.edge_mentions: Dict[str, EdgeMentions] = {}

    def _get_edge_key(self, source: str, target: str, type: str) -> str:
        return f"{source}|{target}|{type}"

    def add_mention(
        self, source: str, target: str, type: str, timestamp: datetime
    ) -> None:
        key = self._get_edge_key(source, target, type)
        if key not in self.edge_mentions:
            self.edge_mentions[key] = EdgeMentions(
                source=source, target=target, type=type, timestamps=[timestamp]
            )
        else:
            self.edge_mentions[key].timestamps.append(timestamp)

    def _calculate_decay(self, last_mention: datetime, current_time: datetime) -> float:
        time_diff = current_time - last_mention

        if time_diff <= timedelta(hours=1):
            decay = math.exp(
                -self.decay_factors["hour"] * time_diff.total_seconds() / 3600
            )
        elif time_diff <= timedelta(days=1):
            decay = math.exp(
                -self.decay_factors["day"] * time_diff.total_seconds() / 86400
            )
        else:
            decay = math.exp(-self.decay_factors["week"] * time_diff.days / 7)

        return max(0.1, decay)

    def _calculate_boost(self, num_mentions: int) -> float:
        return 1 - math.exp(-self.saturation_factor * num_mentions)

    def get_edge_weight(
        self,
        source: str,
        target: str,
        type: str,
        current_time: Optional[datetime] = None,
    ) -> float:
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        key = self._get_edge_key(source, target, type)
        if key not in self.edge_mentions:
            return 0.3  # Peso base per nuove relazioni

        edge = self.edge_mentions[key]

        if not edge.timestamps:
            return 0.3

        last_mention = max(edge.timestamps)
        decay = self._calculate_decay(last_mention, current_time)
        boost = self._calculate_boost(len(edge.timestamps))

        weight = edge.base_weight * decay * boost
        return min(1.0, max(0.1, weight))  # Mantiene sempre un peso minimo

    def get_all_edge_weights(
        self, current_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Restituisce tutti gli archi con i loro pesi aggiornati"""
        if current_time is None:
            current_time = datetime.now()

        weighted_edges = []
        for key, edge in self.edge_mentions.items():
            weight = self.get_edge_weight(
                edge.source, edge.target, edge.type, current_time
            )
            if weight > 0:  # includiamo solo archi con peso > 0
                weighted_edges.append(
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "type": edge.type,
                        "weight": weight,
                        "mentions": len(edge.timestamps),
                    }
                )

        return weighted_edges
