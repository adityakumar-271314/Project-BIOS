from collections import deque


class EventDelayQueue:

    def __init__(
        self,
        delay_ticks: int = 180,
    ):
        self.delay_ticks = delay_ticks

        self._pending = deque()

    def add_candidate(
        self,
        tick: int,
    ):

        self._pending.append(tick)

    def get_ready(
        self,
        current_tick: int,
    ):
        ready = []

        while self._pending:
            # Check the tick attribute of the candidate object
            candidate = self._pending[0]
            candidate_tick = candidate.tick if hasattr(candidate, "tick") else candidate

            if current_tick - candidate_tick < self.delay_ticks:
                break

            ready.append(self._pending.popleft())

        return ready