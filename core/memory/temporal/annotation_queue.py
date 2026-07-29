from collections import deque
from typing import List
from ..schemas import TickSnapshot


class AnnotationQueue:
    """
    Buffers incoming raw TickSnapshots before annotation.

    Supports a configurable tick delay to allow delayed sensor processing,
    async signal alignment, or retrospection windows prior to framing.
    """

    def __init__(self, delay_ticks: int = 0) -> None:
        self.delay_ticks = delay_ticks
        self._queue: deque[TickSnapshot] = deque()

    def enqueue(self, snapshot: TickSnapshot) -> None:
        """Appends a new snapshot to the queue."""
        self._queue.append(snapshot)

    def pop_ready(self, current_tick: int) -> List[TickSnapshot]:
        """
        Extracts and returns all snapshots that meet or exceed the processing delay.
        """
        ready: List[TickSnapshot] = []
        while self._queue:
            head = self._queue[0]
            if current_tick - head.tick < self.delay_ticks:
                break
            ready.append(self._queue.popleft())
        return ready

    def clear(self) -> None:
        """Flushes all queued snapshots."""
        self._queue.clear()

    def __len__(self) -> int:
        return len(self._queue)
