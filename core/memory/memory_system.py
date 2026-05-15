from asyncio import events

from pygame import event

from .semantic import SemanticMemory
from .episodic import EpisodicMemory


class MemorySystem:

    def __init__(self, config):

        self.semantic = SemanticMemory(config)
        self.episodic = EpisodicMemory(config)

    def update(
        self,
        sensors,
        body,
        emotions,
    ):

        self.semantic.update(sensors)

        self.episodic.update(
            sensors=sensors,
            body=body,
            emotions=emotions,
            semantic_memory=self.semantic,
        )

    def import_state(self, data: dict) -> None:

        self.semantic.import_state(
            data.get("semantic", {})
        )

        self.episodic.import_state(
            data.get("episodic", {})
        )

    def export_state(self) -> dict:

        return {
            "semantic": self.semantic.export_state(),
            "episodic": self.episodic.export_state(),
            "version": 1
        }
    

    def get_spatial_bias(self, position=None, radius=None):

        return self.semantic.get_spatial_bias(
            position=position,
            radius=radius,
        )

    def get_debug_memories(self):

        return self.episodic.get_debug_memories()

    @property
    def position(self):

        return self.semantic.position

    @property
    def velocity(self):

        return self.semantic.velocity

    @property
    def landmarks(self):

        return self.semantic.landmarks
    @property
    def internal_pos(self):
        return self.semantic.internal_pos


    @property
    def internal_vel(self):
        return self.semantic.internal_vel
    
    def recall_recent(self, limit: int = 10):
        events = self.episodic.get_events()
        return list(events[-limit:])

    def recall_by_type(
        self,
        event_type: str,
        limit: int | None = None,
    ):

        matches = [
            event
            for event in self.episodic.get_events()
            if event.event_type == event_type
        ]

        if limit is not None:
            matches = matches[-limit:]
            
        return matches
        
    def recall_significant(
        self,
        min_significance: float = 5.0,
    ):

        return [
            event
            for event in self.episodic.get_events()
            if event.significance >= min_significance
        ]
    def recall_near(
        self,
        pos_x: float,
        pos_y: float,
        radius: float,
    ):

        radius_sq = radius * radius

        matches = []

        for event in self.episodic.get_events():

            dx = event.pos_x - pos_x
            dy = event.pos_y - pos_y

            dist_sq = dx * dx + dy * dy

            if dist_sq <= radius_sq:
                matches.append(event)

        return matches
    
    def recall_latest(self):
        events = self.episodic.get_events()
        if not events:
            return None
        return events[-1]
    def last_significant_event(
        self,
        min_significance: float = 5.0,
    ):
        matches = self.recall_significant(min_significance)

        if not matches:
            return None

        return matches[-1]

    def last_danger_event(self):

        danger_types = {
            "danger_state",
            "hazard_encounter",
            "damage_spike",
            "near_death",
        }

        matches = [
            event
            for event in self.episodic.get_events()
            if event.event_type in danger_types
        ]

        if not matches:
            return None

        return matches[-1]

    def last_food_recovery(self):

        matches = self.recall_by_type(
            "food_recovery",
            limit=1,
        )

        if not matches:
            return None

        return matches[-1]

    def most_significant_event(self):

        events = self.episodic.get_events()

        if not events:
            return None

        return max(
            events,
            key=lambda event: event.significance,
        )

    def nearby_danger_memories(
        self,
        pos_x: float,
        pos_y: float,
        radius: float,
    ):
        danger_types = {
            "danger_state",
            "hazard_encounter",
            "damage_spike",
            "near_death",
        }

        nearby = self.recall_near(
            pos_x=pos_x,
            pos_y=pos_y,
            radius=radius,
        )

        return [
            event
            for event in nearby
            if event.event_type in danger_types
        ]