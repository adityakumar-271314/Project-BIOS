from pathlib import Path
import math
from core.memory.storage.loader import EpisodeLoader
from core.memory.reconstruction.reconstruct import EpisodeReconstructor
from tools.episode_visualizer.replay_session import ReplaySession, ReplayTick
from tools.episode_visualizer.raw_extractor import RawTelemetryExtractor

def load_from_storage(episode_folder_path: str | Path) -> ReplaySession:
    folder = Path(episode_folder_path)

    if not folder.exists() or not (folder / "episode.json").exists():
        raise ValueError(f"Corrupted or missing episode structures at {folder}")

    loader = EpisodeLoader()
    episodic_event = loader.load(folder)

    root_telemetry_file = Path.cwd() / "telemetry.jsonl" 
    extractor = RawTelemetryExtractor(root_telemetry_file)
    raw_path_list, raw_metric_map = extractor.extract_range(episodic_event.start_tick, episodic_event.end_tick)

    reconstructor = EpisodeReconstructor()
    reconstructed_ticks = reconstructor.reconstruct(episodic_event)

    if not reconstructed_ticks:
        raise ValueError("Reconstruction produced an empty sequence of frame ticks.")

    validated_ticks = []
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    

    for idx, rt in enumerate(reconstructed_ticks):
        if not all(hasattr(rt, k) for k in ['tick', 'pos_x', 'pos_y', 'heading']):
            raise ValueError("Corrupted tick data: missing geometric components.")
            
        x, y = float(rt.pos_x), float(rt.pos_y)
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
        
        # Calculate drift if corresponding raw data point exists
        drift_val = 0.0
        if idx < len(raw_path_list):
            raw_x, raw_y = raw_path_list[idx]
            drift_val = math.sqrt((x - raw_x) ** 2 + (y - raw_y) ** 2)

        validated_ticks.append(
            ReplayTick(
                tick=int(rt.tick), pos_x=x, pos_y=y, heading=float(rt.heading),
                energy=float(rt.energy), integrity=float(rt.integrity),
                stress=float(rt.stress), fear=float(rt.fear), drive=float(rt.drive),
                confidence=float(getattr(rt, 'confidence', 1.0)),
                anchor=bool(getattr(rt, 'anchor', False)),
                drift=drift_val
            )
        )

    # Bind extracted raw telemetry collections directly into the visual session
    session = ReplaySession(
        name=f"Episode: {episodic_event.event_type} ({episodic_event.start_tick}-{episodic_event.end_tick})",
        episode_id=f"{episodic_event.start_tick}",
        ticks=tuple(validated_ticks),
        duration=(episodic_event.end_tick - episodic_event.start_tick) * 0.1,
        statistics=episodic_event.to_dict().get("state", {}),
        camera_bounds=(min_x - 10, min_y - 10, max_x + 10, max_y + 10),
        metadata=episodic_event.to_dict().get("metadata", {}),
        raw_path=tuple(raw_path_list),
        raw_metrics=raw_metric_map
    )
    
    if not session.validate():
        raise ValueError("ReplaySession structural integrity check failed.")
        
    return session