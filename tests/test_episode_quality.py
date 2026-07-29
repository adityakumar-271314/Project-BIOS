from core.memory.schemas import (
    EpisodicEvent,
    EpisodeSignature,
    TickSnapshot,
    SparseFrame,
    BehavioralTransition,
    StateSummary,
)
from core.memory.quality import EpisodeQuality, EpisodeQualityEvaluator
from core.memory.quality.coherence import CoherenceEvaluator
from core.memory.quality.coverage import CoverageEvaluator
from core.memory.quality.redundancy import RedundancyEvaluator
from core.memory.quality.novelty import NoveltyEvaluator
from core.memory.quality.recall import RecallUsefulnessEvaluator


def _create_mock_snapshot(tick: int) -> TickSnapshot:
    return TickSnapshot(
        tick=tick,
        pos_x=0.0,
        pos_y=0.0,
        vel_x=0.0,
        vel_y=0.0,
        heading=0.0,
        energy=100.0,
        integrity=100.0,
        stress=0.0,
        fear=0.0,
        drive=0.0,
    )


def _create_mock_event(
    start_tick: int = 10,
    end_tick: int = 100,
    dominant_goal: str | None = "explore",
    dominant_skill: str | None = "patrol",
    goal_transitions: tuple = (),
    skill_transitions: tuple = (),
    keyframe_ticks: tuple = (10, 50, 100),
    outcome_completed: bool = True,
    notes: str | None = None,
) -> EpisodicEvent:
    snap = _create_mock_snapshot(start_tick)
    keyframes = [
        SparseFrame(
            tick=t,
            pos_x=0.0,
            pos_y=0.0,
            vel_x=0.0,
            vel_y=0.0,
            heading=0.0,
            energy=100.0,
            integrity=100.0,
            stress=0.0,
            fear=0.0,
            drive=0.0,
            significance=0.8,
        )
        for t in keyframe_ticks
    ]

    summary = StateSummary(initial=100.0, final=90.0, min_val=80.0, max_val=100.0)

    sig = EpisodeSignature(
        dominant_goal=dominant_goal,
        dominant_skill=dominant_skill,
        goal_transitions=goal_transitions,
        skill_transitions=skill_transitions,
        outcome_completed=outcome_completed,
        resource_summaries={"energy": summary, "integrity": summary},
        emotion_summaries={"fear": summary, "stress": summary, "drive": summary},
        duration_ticks=end_tick - start_tick + 1,
        keyframe_ticks=keyframe_ticks,
    )

    return EpisodicEvent(
        start_tick=start_tick,
        peak_tick=(start_tick + end_tick) // 2,
        end_tick=end_tick,
        event_type="test_event",
        peak_significance=0.8,
        start_x=0.0,
        start_y=0.0,
        peak_x=0.0,
        peak_y=0.0,
        end_x=0.0,
        end_y=0.0,
        max_fear=0.0,
        avg_fear=0.0,
        max_stress=0.0,
        avg_stress=0.0,
        max_drive=0.0,
        avg_drive=0.0,
        energy_delta=-10.0,
        integrity_delta=0.0,
        peak_snapshot=snap,
        key_frames=keyframes,
        signature=sig,
        notes=notes,
    )


# --- UNIT TESTS --- #


def test_coherence_evaluator_oscillation():
    """Verify state ping-pong oscillations are penalized in coherence."""
    evaluator = CoherenceEvaluator()

    # Oscillating goal transitions: A -> B -> A
    oscillating_trans = (
        BehavioralTransition(tick=20, from_state="A", to_state="B"),
        BehavioralTransition(tick=30, from_state="B", to_state="A"),
        BehavioralTransition(tick=40, from_state="A", to_state="B"),
        BehavioralTransition(tick=50, from_state="B", to_state="A"),
    )

    event = _create_mock_event(
        start_tick=1, end_tick=100, goal_transitions=oscillating_trans
    )
    score, reasons = evaluator.evaluate(event)

    assert score < 0.7
    assert any("oscillation" in r for r in reasons)


def test_coverage_evaluator_short_duration():
    """Verify short/truncated episodes receive coverage penalties."""
    evaluator = CoverageEvaluator()
    short_event = _create_mock_event(
        start_tick=1, end_tick=3, keyframe_ticks=(1,), notes="truncated episode"
    )
    score, reasons = evaluator.evaluate(short_event)

    assert score < 0.8
    assert "short_or_truncated_duration" in reasons


def test_redundancy_evaluator_duplicates():
    """Verify near-identical overlapping episodes trigger high redundancy."""
    evaluator = RedundancyEvaluator()
    ev1 = _create_mock_event(start_tick=10, end_tick=100)
    ev2 = _create_mock_event(start_tick=12, end_tick=102)

    score, reasons = evaluator.evaluate(ev1, neighbors=[ev2])

    assert score > 0.7
    assert any("high_behavioral_overlap" in r for r in reasons)


def test_quality_orchestrator_end_to_end():
    """Verify EpisodeQualityEvaluator produces valid scores and attaches them."""
    orchestrator = EpisodeQualityEvaluator()
    events = [
        _create_mock_event(start_tick=10, end_tick=100),
        _create_mock_event(start_tick=150, end_tick=250, dominant_goal="forage"),
    ]

    evaluated = orchestrator.evaluate_batch(events)

    assert len(evaluated) == 2
    for ev in evaluated:
        assert ev.quality is not None
        assert isinstance(ev.quality, EpisodeQuality)
        assert 0.0 <= ev.quality.overall_quality <= 1.0
        assert isinstance(ev.quality.reasons, tuple)


def test_quality_serialization_roundtrip():
    """Verify EpisodicEvent to_dict/from_dict preserves quality metrics correctly."""
    orchestrator = EpisodeQualityEvaluator()
    event = _create_mock_event()
    orchestrator.evaluate_batch([event])

    serialized = event.to_dict()
    reconstructed = EpisodicEvent.from_dict(serialized)

    assert reconstructed.quality is not None
    assert reconstructed.quality.overall_quality == event.quality.overall_quality
    assert reconstructed.quality.coherence == event.quality.coherence
    assert reconstructed.quality.reasons == event.quality.reasons
