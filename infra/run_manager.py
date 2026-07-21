from dataclasses import dataclass
import json
from pathlib import Path
from infra.world_state import WorldState
from infra.constants import SPAWN_OFFSET_X, SPAWN_OFFSET_Y

WORLD_STATE_FILE = "world_state.json"


@dataclass(frozen=True)
class RunContext:
    run_dir: Path

    @property
    def world_state(self) -> Path:
        return self.run_dir / "world_state.json"

    @property
    def spatial_memory(self) -> Path:
        return self.run_dir / "spatial_memory_state.json"

    @property
    def telemetry(self) -> Path:
        return self.run_dir / "telemetry.json"

    @property
    def replay(self) -> Path:
        return self.run_dir / "replay.json"

    @property
    def episodes_dir(self) -> Path:
        return self.run_dir / "episodes"


def setup_run_session(base_dir="run_history", default_run_id=None) -> RunContext:
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    
    if default_run_id:
        run_path = base_path / f"run{int(default_run_id):06d}"
        run_path.mkdir(parents=True, exist_ok=True)
        return RunContext(run_dir=run_path)

    print("\n--- BIOS SESSION MANAGER ---")
    print("1. Start a fresh new run session")
    print("2. Continue from an existing run session")
    choice = input("Select option (1-2): ").strip()
    if choice not in {"1", "2"}:
        print("Invalid choice. Defaulting to fresh run.")
        choice = "1"

    if choice == "2":
        existing_runs = sorted([p for p in base_path.iterdir() if p.is_dir() and p.name.startswith("run")])
        if existing_runs:
            print("\nAvailable runs:")
            for idx, run in enumerate(existing_runs):
                print(f"  [{idx}] {run.name}")
            try:
                run_idx = int(input(f"Choose run index (0-{len(existing_runs)-1}): ").strip())
                return RunContext(run_dir=existing_runs[run_idx])
            except (ValueError, IndexError):
                print("Invalid index. Defaulting to fresh run.")
        else:
            print("No existing run folders detected. Creating fresh.")

    existing_ids = [int(p.name.replace("run", "")) for p in base_path.iterdir() if p.is_dir() and p.name.startswith("run")]
    next_id = max(existing_ids) + 1 if existing_ids else 1
    run_path = base_path / f"run{next_id:06d}"
    run_path.mkdir(parents=True, exist_ok=True)
    return RunContext(run_dir=run_path)


def load_world_state(ctx: RunContext, world_seed: int) -> WorldState:
    state_path = ctx.world_state
    run_id = int(ctx.run_dir.name.replace("run", ""))

    if state_path.exists():
        state = WorldState.load(state_path)
        state.continuation = True
        return state

    return WorldState(
        run_id=run_id,
        world_seed=world_seed,
        continuation=False,
    )