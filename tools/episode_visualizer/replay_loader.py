from pathlib import Path
from core.memory.storage.loader import EpisodeLoader
from core.memory.reconstruction.reconstruct import EpisodeReconstructor
from tools.episode_visualizer.replay_session import ReplaySession, ReplayTick

def load_from_storage(episode_folder_path: str | Path) -> ReplaySession:
    folder = Path(episode_folder_path)

    if not folder.exists() or not (folder / "episode.json").exists():
        raise ValueError(f"Corrupted or missing episode structures at {folder}")

    loader = EpisodeLoader()
    episodic_event = loader.load(folder)

    reconstructor = EpisodeReconstructor()
    reconstructed_ticks = reconstructor.reconstruct(episodic_event)

    if not reconstructed_ticks:
        raise ValueError("Reconstruction produced an empty sequence of frame ticks.")

    validated_ticks = []
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for rt in reconstructed_ticks:
        # Strict validation checks on critical visual requirements
        if not all(hasattr(rt, k) for k in ['tick', 'pos_x', 'pos_y', 'heading']):
            raise ValueError("Corrupted tick data: missing geometric components.")
            
        x, y = float(rt.pos_x), float(rt.pos_y)
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
        
        validated_ticks.append(
            ReplayTick(
                tick=int(rt.tick),
                pos_x=x,
                pos_y=y,
                heading=float(rt.heading),
                energy=float(rt.energy),
                integrity=float(rt.integrity),
                stress=float(rt.stress),
                fear=float(rt.fear),
                drive=float(rt.drive),
                confidence=float(getattr(rt, 'confidence', 1.0)),
                anchor=bool(getattr(rt, 'anchor', False))
            )
        )

    session = ReplaySession(
        name=f"Episode: {episodic_event.event_type} ({episodic_event.start_tick}-{episodic_event.end_tick})",
        episode_id=f"{episodic_event.start_tick}",
        ticks=tuple(validated_ticks),
        duration=(episodic_event.end_tick - episodic_event.start_tick) * 0.1,
        statistics=episodic_event.to_dict().get("state", {}),
        camera_bounds=(min_x - 10, min_y - 10, max_x + 10, max_y + 10),
        metadata=episodic_event.to_dict().get("metadata", {})
    )
    
    if not session.validate():
        raise ValueError("ReplaySession structural integrity check failed.")
        
    return session