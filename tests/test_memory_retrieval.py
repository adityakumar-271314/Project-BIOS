from core.memory.memory_system import MemorySystem
from infra.config_loader import load_config
from core.memory.temporal.temporal_buffer import TemporalBuffer
from core.memory.event_delay import EventDelayQueue
from core.memory.episodic import EpisodicMemory

from tests.test_memory import make_snapshot


def test_build_frame_updates_statistics():
    mem = EpisodicMemory(load_config().memory)

    a = make_snapshot(
        tick=1,
        energy=100,
    )

    b = make_snapshot(
        tick=2,
        energy=95,
    )

    before = mem._stats["energy_delta"].n

    frame = mem.build_frame(a, b)

    after = mem._stats["energy_delta"].n

    assert after == before + 1
    assert frame.snapshot.tick == 2


def test_delay_queue_waits():
    q = EventDelayQueue(delay_ticks=5)

    q.add_candidate(10)

    assert q.get_ready(14) == []
    assert q.get_ready(15) == [10]


def test_delay_queue_multiple_ready():
    q = EventDelayQueue(delay_ticks=5)

    q.add_candidate(1)
    q.add_candidate(3)
    q.add_candidate(10)

    ready = q.get_ready(8)

    assert ready == [1, 3]


def test_context_lookup():
    tb = TemporalBuffer()

    for i in range(10):
        tb.append_snapshot(make_snapshot(tick=i))

    context = tb.get_context(5, 2, 2)

    ticks = [s.tick for s in context]

    assert ticks == [3, 4, 5, 6, 7]


from core.memory.episode_builder import EpisodeBuilder


def test_builder_returns_empty_without_peak():
    builder = EpisodeBuilder()

    frames = []

    assert builder.build(frames) == []


def test_recall_latest_empty():
    cfg = load_config()
    memory = MemorySystem(cfg.memory)
    latest = memory.recall_latest()
    assert latest is None
