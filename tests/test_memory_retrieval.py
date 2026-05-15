from core.memory.memory_system import MemorySystem
from core.memory.schemas import EpisodicEvent
from core.config_loader import load_config


def make_event(tick, event_type, significance, x, y):
    return EpisodicEvent(
        tick=tick,
        event_type=event_type,
        significance=significance,
        pos_x=x,
        pos_y=y,
        energy=50.0,
        integrity=80.0,
        stress=0.2,
        fear=0.3,
        drive=0.4,
        energy_delta=-1.0,
        integrity_delta=-2.0,
        stress_delta=0.1,
        fear_delta=0.2,
        drive_delta=0.3,
    )


def build_memory():
    cfg = load_config()
    memory = MemorySystem(cfg.memory)
    memory.episodic.events.extend(
        [
            make_event(1, "food_recovery", 2.0, 0.0, 0.0),
            make_event(2, "danger_state", 8.0, 10.0, 10.0),
            make_event(3, "danger_state", 6.5, 15.0, 15.0),
            make_event(4, "damage_spike", 9.5, 100.0, 100.0),
            make_event(5, "food_recovery", 3.0, -5.0, -5.0),
        ]
    )
    return memory


def test_recall_recent_default():
    memory = build_memory()
    results = memory.recall_recent()
    assert len(results) == 5
    assert results[-1].tick == 5


def test_recall_recent_limit():
    memory = build_memory()
    results = memory.recall_recent(limit=2)
    assert len(results) == 2
    assert results[0].tick == 4
    assert results[1].tick == 5


def test_recall_by_type():
    memory = build_memory()
    results = memory.recall_by_type("danger_state")
    
    assert len(results) == 2
    assert all(event.event_type == "danger_state" for event in results)
    assert results[0].tick == 2
    assert results[1].tick == 3


def test_recall_by_type_limit():
    memory = build_memory()
    results = memory.recall_by_type("danger_state", limit=1)
    
    assert len(results) == 1
    assert results[0].tick == 3


def test_recall_significant():
    memory = build_memory()
    results = memory.recall_significant(min_significance=7.0)
    assert len(results) == 2
    assert results[0].significance >= 7.0
    assert results[1].significance >= 7.0


def test_recall_near():
    memory = build_memory()
    results = memory.recall_near(pos_x=10.0, pos_y=10.0, radius=8.0)
    ticks = [event.tick for event in results]
    assert 2 in ticks
    assert 3 in ticks
    assert 1 not in ticks
    assert 4 not in ticks


def test_recall_near_boundary():
    memory = build_memory()
    results = memory.recall_near(pos_x=0.0, pos_y=0.0, radius=0.0)
    assert len(results) == 1
    assert results[0].tick == 1


def test_recall_latest():
    memory = build_memory()
    latest = memory.recall_latest()
    assert latest is not None
    assert latest.tick == 5


def test_recall_latest_empty():
    cfg = load_config()
    memory = MemorySystem(cfg.memory)
    latest = memory.recall_latest()
    assert latest is None


def test_get_events_returns_immutable_view():
    memory = build_memory()
    events = memory.episodic.get_events()
    assert isinstance(events, tuple)
    original_count = len(memory.episodic.events)
    events = events[:-1]
    assert len(memory.episodic.events) == original_count
