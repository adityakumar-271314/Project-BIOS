import tempfile
import shutil
from pathlib import Path
from core.memory.schemas import EpisodicEvent, EpisodeSignature, EpisodeQuality, OutcomeStatus, HierarchyLevel
from core.memory.episodic import EpisodicMemory

class ConfigMock:
    def __init__(self, root: Path):
        self.episode_root = root

def test_hierarchical_memory_pipeline():
    # Setup temporary run history directory
    temp_dir = tempfile.mkdtemp()
    run_root = Path(temp_dir) / "run_history" / "run000001"
    
    try:
        config = ConfigMock(run_root)
        memory = EpisodicMemory(config)
        memory.initialize_run_state(continuation=False)

        # 1. Create synthetic episodic events with varying goals and spatial anchors
        event1 = EpisodicEvent(
            start_tick=10,
            peak_tick=50,
            end_tick=100,
            event_type="hazard_encounter",
            peak_significance=0.85,
            start_x=0.0, start_y=0.0,
            peak_x=10.0, peak_y=10.0,
            end_x=20.0, end_y=20.0,
            signature=EpisodeSignature(
                dominant_goal="explore_sector",
                dominant_skill="navigate",
                dominant_target="landmark_A",
                outcome_status=OutcomeStatus.COMPLETED,
                nearest_landmark_id=101,
                max_hazard_exposure=0.6,
            ),
            quality=EpisodeQuality(coherence=0.9, overall_quality=0.8)
        )

        event2 = EpisodicEvent(
            start_tick=105,
            peak_tick=150,
            end_tick=200,
            event_type="recovery_action",
            peak_significance=0.75,
            start_x=20.0, start_y=20.0,
            peak_x=25.0, peak_y=25.0,
            end_x=30.0, end_y=30.0,
            signature=EpisodeSignature(
                dominant_goal="explore_sector",
                dominant_skill="heal",
                dominant_target="landmark_A",
                outcome_status=OutcomeStatus.COMPLETED,
                nearest_landmark_id=101,
                max_hazard_exposure=0.1,
            ),
            quality=EpisodeQuality(coherence=0.95, overall_quality=0.85)
        )

        # 2. Encode events into episodic memory (triggers archive save and hierarchical clustering)
        memory.encode(event1)
        memory.encode(event2)

        # 3. Verify Decoupled Persistence
        hierarchy_index_path = run_root / "hierarchy_index.json"
        metadata_index_path = run_root / "metadata_index.json"
        manifest_path = run_root / "manifest.json"
        episode_json_path = run_root / "episodes" / "episode000001" / "episode.json"

        assert hierarchy_index_path.exists(), "hierarchy_index.json must be persisted"
        assert metadata_index_path.exists(), "metadata_index.json must be persisted"
        assert manifest_path.exists(), "manifest.json must be persisted"
        assert episode_json_path.exists(), "episode.json payload must be isolated in episodes/"

        # 4. Verify Zero-Load Top-Down Retrieval
        retrieved_events = memory.retrieve_top_down(
            target_goal="explore_sector",
            min_quality=0.5,
            top_k=2
        )
        assert len(retrieved_events) == 2, "Top-down retrieval should return matching candidates"
        assert retrieved_events[0].signature.dominant_goal == "explore_sector"

        # 5. Verify State Export & Import (Run Continuation Support)
        exported_state = memory.export_state()
        assert "hierarchy" in exported_state
        assert "index" in exported_state

        # Instantiate a new memory instance and import state
        new_memory = EpisodicMemory(config)
        new_memory.initialize_run_state(continuation=True, episodes_dir=run_root)
        new_memory.import_state(exported_state)

        events_after_import = new_memory.get_events()
        assert len(events_after_import) == 2, "Imported state should restore all encoded episodes"

        print("[VERIFICATION SUCCESS] Multi-tier hierarchical memory, persistence, and zero-load retrieval successfully verified!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_hierarchical_memory_pipeline()