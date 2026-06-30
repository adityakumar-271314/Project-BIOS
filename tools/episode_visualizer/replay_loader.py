from pathlib import Path
from core.memory.storage.loader import EpisodeLoader
from core.memory.reconstruction.reconstruct import EpisodeReconstructor
from .replay_session import ReplaySession

def load_from_storage(episode_folder_path: str | Path) -> ReplaySession:
    """Loads a structural episode from storage and executes a live reconstruction pipeline."""
    folder = Path(episode_folder_path)

    # 1. Structural Validation Error Policy Check
    if not folder.exists() or not (folder / "episode.json").exists():
        raise ValueError(f"Corrupted or missing episode structures at {folder}")

    # 2. Extract raw episodic storage elements
    loader = EpisodeLoader()
    episodic_event = loader.load(folder)

    # 3. Live reconstruction execution sequence (No Caching)
    reconstructor = EpisodeReconstructor()
    reconstructed_ticks = reconstructor.reconstruct(episodic_event)

    if not reconstructed_ticks:
        raise ValueError("Reconstruction produced an empty sequence of frame ticks.")
    
    else:
        print(f"Reconstruction completed successfully with {len(reconstructed_ticks)} ticks.")

    # 4. Convert structures to serializable dictionary format
    ticks = []
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for rt in reconstructed_ticks:
        # Dynamic Camera Bounds Parsing
        min_x, max_x = min(min_x, rt.pos_x), max(max_x, rt.pos_x)
        min_y, max_y = min(min_y, rt.pos_y), max(max_y, rt.pos_y)
        
        ticks.append({
            "tick": rt.tick,
            "pos_x": rt.pos_x,
            "pos_y": rt.pos_y,
            "heading": rt.heading,
            "energy": rt.energy,
            "integrity": rt.integrity,
            "stress": rt.stress,
            "fear": rt.fear,
            "drive": rt.drive,
            "confidence": rt.confidence,
            "anchor": rt.anchor
        })
        
    return ReplaySession(
        name=f"Episode: {episodic_event.event_type} ({episodic_event.start_tick}-{episodic_event.end_tick})",
        episode_id=f"{episodic_event.start_tick}",
        ticks=ticks,
        duration=(episodic_event.end_tick - episodic_event.start_tick) * 0.1,
        statistics=episodic_event.to_dict().get("state", {}),
        camera_bounds=(min_x - 10, min_y - 10, max_x + 10, max_y + 10)
    )