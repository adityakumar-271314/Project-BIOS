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