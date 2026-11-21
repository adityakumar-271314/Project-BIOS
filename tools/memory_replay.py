#!/usr/bin/env python3
"""
Offline Memory Replay for Project BIOS.

Re-feeds a recorded run (``run_history/runXXXXXX/replay.json`` + ``telemetry.json``)
through ``MemorySystem`` WITHOUT Godot, the TCP bridge, the Brain or motor policies,
and writes every output into a separate mirrored folder
(``re_run_history/runXXXXXX/``). The source run is only ever read.

Usage
-----
    python tools/memory_replay.py --run 1
    python tools/memory_replay.py -r run000001 --tag expA
    python tools/memory_replay.py                      # interactive run picker
    use --visualize for spatial_map
What is reconstructed, and how
------------------------------
* ``sensors``   - rebuilt from ``replay.json`` WITHOUT re-applying the Godot->internal
                  sign flips (``SensorPacket.to_dict`` already stores internal values).
* ``body``      - ``energy``/``integrity`` from ``telemetry.json``. Telemetry is written
                  AFTER ``agent.tick`` (i.e. after ``bst.update``) while ``memory.update``
                  runs BEFORE it, so by default body values lag one tick
                  (``--body-alignment lag1``). Tick 1 of a fresh run uses the real
                  initial ``BodyStateTracker`` values.
* ``emotions``  - ``stress``/``fear``/``drive`` from ``telemetry.json`` (same tick; the
                  emotion engine updates before ``memory.update``).
* ``active_goal`` / ``active_skill`` / ``target`` - NOT recorded anywhere, so they are
                  passed as ``None``. Episodes are therefore detected from vitals,
                  sensors and spatial data only; goal/skill transitions and the
                  ``dominant_goal`` / ``dominant_skill`` signature fields stay empty.
                  A replay is NOT guaranteed to reproduce the live episode set.

Fidelity self-check: after every successful frame the replayed spatial position,
velocity, landmark count and grid-cell count are compared with the recorded telemetry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterator, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.memory.memory_system import MemorySystem  # noqa: E402
from core.vector import Vector2  # noqa: E402
from infra.config_loader import load_config  # noqa: E402
from infra.constants import DEFAULT_DELTA, MAX_ENERGY, MAX_INTEGRITY  # noqa: E402
from infra.data_models import SensedObject, SensorPacket  # noqa: E402
from infra.run_manager import RunContext  # noqa: E402
from tools.visualizer import run_visualizer
from time import sleep

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

SOURCE_DIRNAME = "run_history"
OUTPUT_DIRNAME = "re_run_history"
SUMMARY_FILENAME = "replay_summary.json"

# Layout written by core/memory/storage/* (see EpisodeSerializer / EpisodeArchive)
MANIFEST_NAME = "manifest.json"
INDEX_NAME = "memory_index.json"
EPISODE_DIR_RE = re.compile(r"^episode\d+$")

# Keys SensorPacket.to_dict() always writes
PACKET_KEYS = (
    "delta",
    "accel",
    "ray_c",
    "ray_l",
    "ray_r",
    "current_rotation",
    "is_stuck",
    "hazard_stim",
    "food_stim",
    "real_pos_x",
    "real_pos_y",
    "collision_normals",
    "sensed_objects",
    "is_real_data",
)
VITAL_KEYS = ("energy", "integrity", "stress", "fear", "drive")
CONTEXT_KEYS = (
    "goal_name",
    "goal_priority",
    "active_skill",
    "target_type",
    "target_id",
    "target_x",
    "target_y",
)
POS_TOLERANCE = 1e-6
WARN_CAP = 10


# --------------------------------------------------------------------------- #
# Small utilities
# --------------------------------------------------------------------------- #


class Warner:
    """Prints the first few warnings per category, then only counts them."""

    def __init__(self, cap: int = WARN_CAP) -> None:
        self.cap = cap
        self.counts: Dict[str, int] = defaultdict(int)

    def warn(self, category: str, message: str) -> None:
        self.counts[category] += 1
        n = self.counts[category]
        if n <= self.cap:
            print(f"[WARN] {message}")
        elif n == self.cap + 1:
            print(f"[WARN] ({category}) further warnings of this kind are suppressed")


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sha256_prefix(path: Path, length: int = 12) -> Optional[str]:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:length]
    except OSError:
        return None


def human_size(num: int) -> str:
    size = float(num)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{num} B"


# --------------------------------------------------------------------------- #
# Run selection
# --------------------------------------------------------------------------- #


def normalize_run_token(token: str) -> str:
    """'1' / '000001' / 'run1' / 'run000001' -> 'run000001'. Other names pass through."""
    t = token.strip()
    m = re.fullmatch(r"(?:run)?0*(\d+)", t, flags=re.IGNORECASE)
    if m:
        return f"run{int(m.group(1)):06d}"
    return t


def list_runs(source_root: Path) -> List[Path]:
    if not source_root.is_dir():
        return []
    return sorted(
        p for p in source_root.iterdir() if p.is_dir() and p.name.startswith("run")
    )


def describe_run(run_dir: Path) -> str:
    ctx = RunContext(run_dir=run_dir)
    parts = []
    for label, path in (("replay", ctx.replay), ("telemetry", ctx.telemetry)):
        if path.is_file():
            parts.append(f"{label} {human_size(path.stat().st_size)}")
        else:
            parts.append(f"{label} MISSING")
    return ", ".join(parts)


def choose_run_interactively(source_root: Path) -> Path:
    runs = list_runs(source_root)
    if not runs:
        raise SystemExit(f"[ERROR] No runs found in {source_root}")
    print("\n--- Available runs ---")
    for idx, run in enumerate(runs, start=1):
        print(f"  [{idx}] {run.name}  ({describe_run(run)})")
    while True:
        try:
            raw = input(
                f"Select list number (1-{len(runs)}) or type a run folder name: "
            ).strip()
        except EOFError:
            raise SystemExit(
                "[ERROR] No run selected (no interactive input available)."
            )
        if raw.isdigit() and 1 <= int(raw) <= len(runs):
            return runs[int(raw) - 1]
        candidate = source_root / raw
        if raw.lower().startswith("run") and candidate.is_dir():
            return candidate
        print("  Invalid selection, try again.")


def resolve_run(run_arg: Optional[str], source_root: Path) -> Path:
    if run_arg is None:
        return choose_run_interactively(source_root)
    name = normalize_run_token(run_arg)
    run_dir = source_root / name
    if not run_dir.is_dir():
        known = ", ".join(p.name for p in list_runs(source_root)) or "none"
        raise SystemExit(
            f"[ERROR] Run folder not found: {run_dir}\n        Available: {known}"
        )
    return run_dir


def allocate_output_dir(output_root: Path, run_name: str, tag: Optional[str]) -> Path:
    """
    Never overwrites. First replay -> run000001, then run000001_r2, run000001_r3, ...
    With --tag expA -> run000001_expA, then run000001_expA_r2, ...
    """
    output_root.mkdir(parents=True, exist_ok=True)
    base = run_name
    if tag:
        clean = re.sub(r"[^A-Za-z0-9_-]", "", tag)
        if clean:
            base = f"{run_name}_{clean}"
    attempt = 1
    candidate = output_root / base
    while True:
        try:
            candidate.mkdir(parents=False, exist_ok=False)  # atomic claim
            return candidate
        except FileExistsError:
            attempt += 1
            candidate = output_root / f"{base}_r{attempt}"


def ensure_roots_are_separate(source_root: Path, output_root: Path) -> None:
    s, o = source_root.resolve(), output_root.resolve()
    if s == o or s in o.parents or o in s.parents:
        raise SystemExit(
            f"[ERROR] Output root ({o}) and source root ({s}) must be separate, "
            "non-nested directories."
        )


# --------------------------------------------------------------------------- #
# Source immutability guard
# --------------------------------------------------------------------------- #


def snapshot_tree(root: Path) -> Dict[str, Tuple[int, int]]:
    snap: Dict[str, Tuple[int, int]] = {}
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            snap[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return snap


# --------------------------------------------------------------------------- #
# Streaming readers
# --------------------------------------------------------------------------- #


def iter_jsonl(path: Path) -> Iterator[Tuple[int, Optional[dict], Optional[str]]]:
    """Yields (line_no, obj, error). Both recorders write JSONL (one object/line)."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except ValueError as exc:
                yield line_no, None, f"invalid JSON ({exc})"
                continue
            if not isinstance(obj, dict):
                yield line_no, None, "line is not a JSON object"
                continue
            yield line_no, obj, None


class TelemetryCursor:
    """Lock-step reader: hands out the telemetry row for a given replay tick."""

    def __init__(self, path: Path, warner: Warner) -> None:
        self._it = iter_jsonl(path)
        self._pending: Optional[dict] = None
        self._started = False
        self._done = False
        self._warner = warner
        self.bad_lines = 0
        self.orphan_rows = 0

    def _advance(self) -> None:
        self._started = True
        while True:
            try:
                line_no, obj, err = next(self._it)
            except StopIteration:
                self._pending = None
                self._done = True
                return
            if obj is None or not is_int(obj.get("tick")):
                self.bad_lines += 1
                self._warner.warn(
                    "telemetry_line",
                    f"telemetry.json line {line_no}: {err or 'missing/invalid tick'} - skipped",
                )
                continue
            self._pending = obj
            return

    def take(self, tick: int) -> Optional[dict]:
        if not self._started:
            self._advance()
        while self._pending is not None and self._pending["tick"] < tick:
            self.orphan_rows += 1  # telemetry row with no matching replay frame
            self._advance()
        if self._pending is not None and self._pending["tick"] == tick:
            row = self._pending
            self._advance()
            return row
        return None


# --------------------------------------------------------------------------- #
# SensorPacket reconstruction
# --------------------------------------------------------------------------- #


def packet_from_recorded(d: Dict[str, Any]) -> Tuple[SensorPacket, List[str]]:
    """
    Inverse of SensorPacket.to_dict().

    The recorded dict already holds INTERNAL-frame values, so NO sign flips are applied
    (SensorPacket.from_world_data would negate accel.y, rotation, object angles and
    collision normals a second time and would read position from 'global_x/y' instead
    of 'real_pos_x/y').

    Returns (packet, missing_keys).
    """
    # Safety net: a raw Godot-format dict (not produced by to_dict) must be converted
    # with the real transform instead.
    if "global_x" in d and "real_pos_x" not in d:
        return SensorPacket.from_world_data(d), []

    missing = [k for k in PACKET_KEYS if k not in d]
    accel = d.get("accel") or {}
    normals = [
        Vector2(float(n.get("x", 0.0)), float(n.get("y", 0.0)))
        for n in (d.get("collision_normals") or [])
    ]
    objects = [
        SensedObject(
            id=int(o.get("id", -1)),
            type=str(o.get("type", "unknown")),
            dist=float(o.get("dist", 0.0)),
            angle=float(o.get("angle", 0.0)),
        )
        for o in (d.get("sensed_objects") or [])
    ]
    packet = SensorPacket(
        delta=float(d.get("delta", DEFAULT_DELTA)),
        accel=Vector2(float(accel.get("x", 0.0)), float(accel.get("y", 0.0))),
        ray_c=float(d.get("ray_c", 1.0)),
        ray_l=float(d.get("ray_l", 1.0)),
        ray_r=float(d.get("ray_r", 1.0)),
        current_rotation=float(d.get("current_rotation", 0.0)),
        is_stuck=bool(d.get("is_stuck", False)),
        hazard_stim=float(d.get("hazard_stim", 0.0)),
        food_stim=float(d.get("food_stim", 0.0)),
        real_pos_x=float(d.get("real_pos_x", 0.0)),
        real_pos_y=float(d.get("real_pos_y", 0.0)),
        collision_normals=normals,
        sensed_objects=objects,
        is_real_data=bool(d.get("is_real_data", True)),
    )
    return packet, missing


def read_vitals(row: Optional[dict]) -> Optional[Dict[str, float]]:
    if row is None:
        return None
    out: Dict[str, float] = {}
    for key in VITAL_KEYS:
        value = to_float(row.get(key))
        if value is None:
            return None
        out[key] = value
    return out


def read_context(obj: Dict[str, Any]) -> Tuple[Any, Any, Any, bool]:
    """
    Rebuild (goal, skill, target) for MemorySystem.update from a replay line.
    TemporalBuffer.capture only reads goal.name/.priority, the skill string and
    target.type/.id/.x/.y, so lightweight stand-ins are enough.
    Returns (goal, skill, target, found). Old runs without these keys give (None, None, None, False).
    """
    src = obj.get("agent_context")
    if not isinstance(src, dict):
        src = obj
    if not any(k in src for k in CONTEXT_KEYS):
        return None, None, None, False

    goal_name = src.get("goal_name")
    goal = None
    if goal_name is not None:
        goal = SimpleNamespace(
            name=goal_name, priority=to_float(src.get("goal_priority")) or 0.0
        )

    skill = src.get("active_skill")

    target = None
    if any(
        src.get(k) is not None
        for k in ("target_type", "target_id", "target_x", "target_y")
    ):
        target = SimpleNamespace(
            type=src.get("target_type"),
            id=src.get("target_id"),
            x=src.get("target_x"),
            y=src.get("target_y"),
        )
    return goal, skill, target, True


# --------------------------------------------------------------------------- #
# MemorySystem construction
# --------------------------------------------------------------------------- #


def build_memory_system(memory_cfg: Any) -> MemorySystem:
    """
    EpisodicMemory.__init__ eagerly builds an EpisodeArchive at the relative default
    'core/memory/episodes' (MemoryConfig has no 'episode_root'), which creates folders
    and a manifest.json in the CURRENT WORKING DIRECTORY. Construct inside a throwaway
    scratch directory so nothing stray is written into the project; the real archive is
    created afterwards by initialize_run_state(episodes_dir=...).
    """
    previous_cwd = os.getcwd()
    with tempfile.TemporaryDirectory(prefix="bios_replay_scratch_") as scratch:
        os.chdir(scratch)
        try:
            return MemorySystem(memory_cfg)
        finally:
            os.chdir(previous_cwd)


def initial_body_values(cfg: Any) -> Tuple[float, float]:
    try:
        from core.body import BodyStateTracker  # noqa: WPS433

        bst = BodyStateTracker(cfg.body)
        return float(bst.energy), float(bst.integrity)
    except Exception:
        return float(MAX_ENERGY), float(MAX_INTEGRITY)


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #


@dataclass
class ReplayStats:
    total_ticks: int = 0  # replay.json records read (valid + corrupt)
    successful_frames: int = 0
    error_frames: int = 0
    degraded_frames: int = (
        0  # fed, but telemetry missing/invalid -> vitals carried forward
    )
    partial_packets: int = (
        0  # fed, but some sensor_packet keys were missing (defaults used)
    )
    fallback_packets: int = 0  # recorded with is_real_data == False (bridge error live)
    missing_ticks: int = 0  # gaps in the recorded tick sequence
    tick_regressions: int = 0  # tick <= previous tick (duplicates / session restarts)
    first_tick: Optional[int] = None
    last_tick: Optional[int] = None
    max_consecutive_errors: int = 0
    aborted: bool = False
    interrupted: bool = False
    shutdown_error: Optional[str] = None
    telemetry_orphans: int = 0
    telemetry_bad_lines: int = 0
    elapsed_s: float = 0.0
    context_frames: int = 0


@dataclass
class Fidelity:
    compared: int = 0
    pos_mismatch: int = 0
    max_pos_err: float = 0.0
    max_vel_err: float = 0.0
    first_pos_mismatch_tick: Optional[int] = None
    landmark_mismatch: int = 0
    grid_mismatch: int = 0

    def record(self, memory: MemorySystem, tel: dict, tick: int) -> None:
        sm = memory.spatial_mem
        px, py = to_float(tel.get("pos_x")), to_float(tel.get("pos_y"))
        if px is None or py is None:
            return
        self.compared += 1
        pos = sm.internal_pos
        err = max(abs(pos.x - px), abs(pos.y - py))
        self.max_pos_err = (
            max(self.max_pos_err, err) if err == err else self.max_pos_err
        )
        if not (err <= POS_TOLERANCE):  # also catches NaN
            self.pos_mismatch += 1
            if self.first_pos_mismatch_tick is None:
                self.first_pos_mismatch_tick = tick
        vx, vy = to_float(tel.get("velocity_x")), to_float(tel.get("velocity_y"))
        if vx is not None and vy is not None:
            vel = sm.internal_vel
            verr = max(abs(vel.x - vx), abs(vel.y - vy))
            if verr == verr:
                self.max_vel_err = max(self.max_vel_err, verr)
        lc, gc = tel.get("landmark_count"), tel.get("grid_cells")
        try:
            if is_int(lc) and len(sm.landmarks) != lc:
                self.landmark_mismatch += 1
            if is_int(gc) and len(sm._grid) != gc:
                self.grid_mismatch += 1
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# Replay loop
# --------------------------------------------------------------------------- #


def run_replay(
    memory: MemorySystem,
    cfg: Any,
    replay_path: Path,
    telemetry_path: Path,
    args: argparse.Namespace,
    warner: Warner,
    path_log: Optional[List[Vector2]] = None,
) -> Tuple[ReplayStats, Fidelity]:
    stats = ReplayStats()
    fidelity = Fidelity()
    telemetry = TelemetryCursor(telemetry_path, warner)

    init_energy, init_integrity = initial_body_values(cfg)
    body = SimpleNamespace(energy=init_energy, integrity=init_integrity, is_alive=True)
    emotions = SimpleNamespace(stress=0.0, fear=0.0, drive=0.0)

    consecutive_errors = 0
    prev_tick: Optional[int] = None
    started = time.time()

    try:
        for line_no, obj, err in iter_jsonl(replay_path):
            if args.limit and stats.total_ticks >= args.limit:
                break
            stats.total_ticks += 1

            # ---- parse + validate -------------------------------------------------
            tick: Optional[int] = None
            packet: Optional[SensorPacket] = None
            problem: Optional[str] = err
            if obj is not None:
                tick = obj.get("tick")
                sp = obj.get("sensor_packet")
                if not is_int(tick):
                    problem = f"missing/invalid 'tick' ({tick!r})"
                elif not isinstance(sp, dict):
                    problem = "missing/invalid 'sensor_packet'"
                else:
                    try:
                        packet, missing = packet_from_recorded(sp)
                        if missing:
                            stats.partial_packets += 1
                            warner.warn(
                                "partial_packet",
                                f"tick {tick}: sensor_packet missing keys {missing}; defaults used",
                            )
                    except Exception as exc:
                        problem = f"sensor_packet could not be rebuilt ({exc!r})"

            if problem is not None or packet is None or not is_int(tick):
                stats.error_frames += 1
                consecutive_errors += 1
                stats.max_consecutive_errors = max(
                    stats.max_consecutive_errors, consecutive_errors
                )
                warner.warn(
                    "bad_frame",
                    f"replay.json line {line_no}: {problem} - frame skipped",
                )
                if consecutive_errors >= args.max_consecutive_errors:
                    stats.aborted = True
                    print(
                        f"[ERROR] {consecutive_errors} consecutive bad frames - aborting replay."
                    )
                    break
                continue

            # ---- tick bookkeeping -------------------------------------------------
            if prev_tick is None:
                stats.first_tick = tick
                if tick != 1:
                    warner.warn(
                        "start_tick",
                        f"replay starts at tick {tick}, not 1 (continued/truncated run?). "
                        "MemorySystem is still initialised from scratch.",
                    )
            elif tick <= prev_tick:
                stats.tick_regressions += 1
                warner.warn(
                    "tick_regression",
                    f"tick went {prev_tick} -> {tick} at line {line_no} (duplicate or session restart)",
                )
            elif tick > prev_tick + 1:
                gap = tick - prev_tick - 1
                stats.missing_ticks += gap
                warner.warn(
                    "tick_gap", f"{gap} tick(s) missing between {prev_tick} and {tick}"
                )
            prev_tick = tick
            stats.last_tick = tick

            if not packet.is_real_data:
                stats.fallback_packets += 1

            goal, skill, target, has_ctx = read_context(obj)
            if has_ctx:
                stats.context_frames += 1

            # ---- body / emotions --------------------------------------------------
            tel = telemetry.take(tick)
            vitals = read_vitals(tel)
            if vitals is None:
                stats.degraded_frames += 1
                warner.warn(
                    "no_telemetry",
                    f"tick {tick}: no usable telemetry row - vitals carried forward",
                )
            else:
                if (
                    stats.successful_frames + stats.error_frames == 0
                    and stats.first_tick != 1
                ):
                    # Continued run: true body state at this tick is unknown, so seed
                    # it from telemetry instead of the fresh-run initial values.
                    if path_log is not None:
                        path_log.append(memory.spatial_mem.internal_pos.copy())

                    body.energy, body.integrity = vitals["energy"], vitals["integrity"]
                if args.body_alignment == "same":
                    body.energy, body.integrity = vitals["energy"], vitals["integrity"]
                emotions.stress = vitals["stress"]
                emotions.fear = vitals["fear"]
                emotions.drive = vitals["drive"]
            body.is_alive = body.integrity > 0

            # ---- feed MemorySystem ------------------------------------------------
            try:
                memory.update(
                    sensors=packet,
                    body=body,
                    emotions=emotions,
                    active_goal=goal,
                    active_skill=skill,
                    target=target,
                )
            except Exception as exc:
                stats.error_frames += 1
                consecutive_errors += 1
                stats.max_consecutive_errors = max(
                    stats.max_consecutive_errors, consecutive_errors
                )
                warner.warn(
                    "update_error", f"tick {tick}: MemorySystem.update raised {exc!r}"
                )
                if consecutive_errors == 1 and warner.counts["update_error"] == 1:
                    traceback.print_exc()
                if consecutive_errors >= args.max_consecutive_errors:
                    stats.aborted = True
                    print(
                        f"[ERROR] {consecutive_errors} consecutive update errors - aborting replay."
                    )
                    break
                continue

            consecutive_errors = 0
            stats.successful_frames += 1
            if vitals is not None:
                if args.body_alignment == "lag1":
                    # memory.update runs BEFORE bst.update live, so the NEXT tick sees
                    # this tick's post-update telemetry values.
                    body.energy, body.integrity = vitals["energy"], vitals["integrity"]
                fidelity.record(memory, tel, tick)  # type: ignore[arg-type]

            if args.progress_every and stats.total_ticks % args.progress_every == 0:
                print(
                    f"  ... {stats.total_ticks} ticks "
                    f"(ok={stats.successful_frames}, errors={stats.error_frames})"
                )
    except KeyboardInterrupt:
        stats.interrupted = True
        print("\n[WARN] Interrupted - finalising what has been replayed so far.")

    stats.telemetry_orphans = telemetry.orphan_rows
    stats.telemetry_bad_lines = telemetry.bad_lines
    stats.elapsed_s = time.time() - started
    return stats, fidelity


# --------------------------------------------------------------------------- #
# Artifact verification
# --------------------------------------------------------------------------- #


@dataclass
class ArtifactCheck:
    name: str
    path: str
    status: str  # OK | MISSING | EMPTY | INVALID
    detail: str = ""
    expected: bool = False  # True when absence/emptiness is legitimate (0 episodes)


def _load_json(path: Path) -> Tuple[Optional[Any], Optional[str]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as exc:
        return None, str(exc)


def verify_artifacts(out_dir: Path) -> Tuple[List[ArtifactCheck], List[str]]:
    ctx = RunContext(run_dir=out_dir)
    checks: List[ArtifactCheck] = []
    notes: List[str] = []

    # --- spatial memory -------------------------------------------------------
    sp = ctx.spatial_memory
    if not sp.is_file():
        checks.append(ArtifactCheck("spatial memory", str(sp), "MISSING"))
    elif sp.stat().st_size == 0:
        checks.append(ArtifactCheck("spatial memory", str(sp), "EMPTY"))
    else:
        data, err = _load_json(sp)
        if err:
            checks.append(ArtifactCheck("spatial memory", str(sp), "INVALID", err))
        else:
            detail = human_size(sp.stat().st_size)
            if isinstance(data, dict):
                lm, grid = data.get("landmarks"), data.get("grid")
                if isinstance(lm, dict) and isinstance(grid, dict):
                    detail += f", {len(lm)} landmarks, {len(grid)} grid cells"
            checks.append(ArtifactCheck("spatial memory", str(sp), "OK", detail))

    # --- encoded episodes (count ONLY episodeNNNNNN directories) --------------
    ep_dir = ctx.episodes_dir
    episode_dirs: List[Path] = []
    if ep_dir.is_dir():
        episode_dirs = sorted(
            p for p in ep_dir.iterdir() if p.is_dir() and EPISODE_DIR_RE.match(p.name)
        )
    n_eps = len(episode_dirs)
    if not ep_dir.is_dir():
        checks.append(ArtifactCheck("encoded episodes", str(ep_dir), "MISSING"))
    elif n_eps == 0:
        checks.append(
            ArtifactCheck(
                "encoded episodes",
                str(ep_dir),
                "EMPTY",
                "0 episode folders",
                expected=True,
            )
        )
    else:
        bad = [
            p.name
            for p in episode_dirs
            if not (p / "episode.json").is_file()
            or (p / "episode.json").stat().st_size == 0
        ]
        if bad:
            checks.append(
                ArtifactCheck(
                    "encoded episodes",
                    str(ep_dir),
                    "MISSING",
                    f"{n_eps} folders, but episode.json missing/empty in: {', '.join(bad[:5])}"
                    + (" ..." if len(bad) > 5 else ""),
                )
            )
        else:
            checks.append(
                ArtifactCheck(
                    "encoded episodes", str(ep_dir), "OK", f"{n_eps} episode folder(s)"
                )
            )

    # --- manifest.json --------------------------------------------------------
    mf = ep_dir / MANIFEST_NAME
    next_id: Optional[int] = None
    if not mf.is_file():
        checks.append(ArtifactCheck(MANIFEST_NAME, str(mf), "MISSING"))
    elif mf.stat().st_size == 0:
        checks.append(ArtifactCheck(MANIFEST_NAME, str(mf), "EMPTY"))
    else:
        data, err = _load_json(mf)
        if err or not isinstance(data, dict) or not is_int(data.get("next_episode_id")):
            checks.append(
                ArtifactCheck(
                    MANIFEST_NAME, str(mf), "INVALID", err or "no next_episode_id"
                )
            )
        else:
            next_id = data["next_episode_id"]
            checks.append(
                ArtifactCheck(
                    MANIFEST_NAME, str(mf), "OK", f"next_episode_id={next_id}"
                )
            )

    # --- unified metadata / hierarchy index -----------------------------------
    ix = ep_dir / INDEX_NAME
    index_count: Optional[int] = None
    if not ix.is_file():
        if n_eps == 0:
            checks.append(
                ArtifactCheck(
                    INDEX_NAME,
                    str(ix),
                    "MISSING",
                    "expected: the index is only created on the first episode / hierarchy write",
                    expected=True,
                )
            )
        else:
            checks.append(ArtifactCheck(INDEX_NAME, str(ix), "MISSING"))
    elif ix.stat().st_size == 0:
        checks.append(ArtifactCheck(INDEX_NAME, str(ix), "EMPTY"))
    else:
        data, err = _load_json(ix)
        if (
            err
            or not isinstance(data, dict)
            or not isinstance(data.get("episodes"), list)
        ):
            checks.append(
                ArtifactCheck(
                    INDEX_NAME, str(ix), "INVALID", err or "no 'episodes' list"
                )
            )
        else:
            index_count = len(data["episodes"])
            hier = data.get("hierarchies")
            n_groups = len(hier) if isinstance(hier, dict) else 0
            checks.append(
                ArtifactCheck(
                    INDEX_NAME,
                    str(ix),
                    "OK",
                    f"{index_count} episode entries, {n_groups} hierarchy group(s)",
                )
            )

    # --- consistency cross-checks --------------------------------------------
    if next_id is not None and next_id - 1 != n_eps:
        notes.append(
            f"manifest next_episode_id-1 ({next_id - 1}) != episode folders ({n_eps})"
        )
    if index_count is not None and index_count != n_eps:
        notes.append(
            f"index lists {index_count} episodes but {n_eps} episode folders exist"
        )
    if (ep_dir / "memory_index.json.tmp").exists():
        notes.append("stray memory_index.json.tmp found (an atomic index write failed)")
    legacy = ep_dir / "hierarchy_index.json"
    if legacy.exists():
        notes.append("info: legacy hierarchy_index.json is also present")
    return checks, notes


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def print_summary(
    out_dir: Path,
    source_dir: Path,
    stats: ReplayStats,
    fidelity: Fidelity,
    checks: List[ArtifactCheck],
    notes: List[str],
    source_unchanged: bool,
    source_changes: List[str],
    result: str,
) -> None:
    bar = "=" * 72
    print(f"\n{bar}\nMEMORY REPLAY SUMMARY\n{bar}")
    print(f"Source run (read-only) : {source_dir}")
    print(f"Target re_run_history  : {out_dir}")
    print(f"Tick range             : {stats.first_tick} -> {stats.last_tick}")
    print(f"Total ticks processed  : {stats.total_ticks}")
    print(f"Successful frames      : {stats.successful_frames}")
    print(f"Error frames           : {stats.error_frames}")
    extras = [
        ("degraded (no telemetry)", stats.degraded_frames),
        ("partial sensor packets", stats.partial_packets),
        ("fallback packets (is_real_data=False)", stats.fallback_packets),
        ("missing ticks (gaps)", stats.missing_ticks),
        ("tick regressions", stats.tick_regressions),
        ("orphan telemetry rows", stats.telemetry_orphans),
        ("bad telemetry lines", stats.telemetry_bad_lines),
    ]
    shown = [f"{label}: {n}" for label, n in extras if n]
    if shown:
        print("Data quality notes     : " + "; ".join(shown))
    print(f"Elapsed                : {stats.elapsed_s:.1f}s")
    if stats.context_frames == 0:
        print(
            "Agent context          : NOT recorded in this run (goal/skill/target = None)"
        )
    else:
        print(
            f"Agent context          : {stats.context_frames}/{stats.total_ticks} frames carried goal/skill/target"
        )
    if stats.aborted:
        print("[ERROR] Replay was ABORTED early (too many consecutive errors).")
    if stats.interrupted:
        print("[WARN] Replay was interrupted by the user.")
    if stats.shutdown_error:
        print(f"[ERROR] shutdown_and_save failed: {stats.shutdown_error}")

    print("\nSpatial fidelity vs recorded telemetry:")
    if fidelity.compared == 0:
        print("  (no frames could be compared)")
    else:
        ok = fidelity.compared - fidelity.pos_mismatch
        tag = "[OK]" if fidelity.pos_mismatch == 0 else "[WARN]"
        print(
            f"  {tag} position within {POS_TOLERANCE:g}: {ok}/{fidelity.compared} frames "
            f"(max err {fidelity.max_pos_err:.3g}, max vel err {fidelity.max_vel_err:.3g})"
        )
        if fidelity.first_pos_mismatch_tick is not None:
            print(f"       first divergence at tick {fidelity.first_pos_mismatch_tick}")
        if fidelity.landmark_mismatch or fidelity.grid_mismatch:
            print(
                f"  [WARN] landmark-count mismatches: {fidelity.landmark_mismatch}, "
                f"grid-cell-count mismatches: {fidelity.grid_mismatch}"
            )
        if fidelity.pos_mismatch:
            print(
                "       (config.json may differ from the one used when the run was recorded)"
            )

    print("\nArtifact verification:")
    for c in checks:
        suffix = f" - {c.detail}" if c.detail else ""
        print(f"  [{c.status}] {c.name}: {c.path}{suffix}")
    for n in notes:
        print(f"  [NOTE] {n}")

    print("\nSource run integrity:")
    if source_unchanged:
        print("  [OK] run_history source folder unchanged")
    else:
        print("  [ERROR] source folder CHANGED during replay:")
        for line in source_changes[:10]:
            print(f"        {line}")
    print(f"\nRESULT: {result}\n{bar}")


def decide_result(
    stats: ReplayStats,
    fidelity: Fidelity,
    checks: List[ArtifactCheck],
    source_unchanged: bool,
) -> Tuple[str, int]:
    hard = (
        stats.aborted
        or stats.shutdown_error is not None
        or not source_unchanged
        or stats.successful_frames == 0
        or any(c.status != "OK" and not c.expected for c in checks)
    )
    if hard:
        return "FAIL", 2
    soft = (
        stats.error_frames
        or stats.degraded_frames
        or stats.partial_packets
        or stats.missing_ticks
        or stats.tick_regressions
        or stats.interrupted
        or fidelity.pos_mismatch
        or any(c.status != "OK" for c in checks)
    )
    return ("PASS WITH WARNINGS", 0) if soft else ("PASS", 0)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Replay a recorded BIOS run through MemorySystem (offline, read-only on run_history)."
    )
    p.add_argument(
        "-r",
        "--run",
        help="Run id (e.g. 1) or folder name (e.g. run000001). Omit for a picker.",
    )
    p.add_argument("--source-root", default=str(PROJECT_ROOT / SOURCE_DIRNAME))
    p.add_argument("--output-root", default=str(PROJECT_ROOT / OUTPUT_DIRNAME))
    p.add_argument("--config", default=str(PROJECT_ROOT / "config.json"))
    p.add_argument(
        "--tag", help="Optional label appended to the output folder (run000001_<tag>)."
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Replay only the first N ticks (debugging).",
    )
    p.add_argument(
        "--body-alignment",
        choices=("lag1", "same"),
        default="lag1",
        help="lag1: memory sees the previous tick's post-update body values (matches agent.tick order). "
        "same: use this tick's telemetry body values.",
    )
    p.add_argument("--max-consecutive-errors", type=int, default=50)
    p.add_argument(
        "--progress-every", type=int, default=5000, help="0 disables progress lines."
    )
    p.add_argument(
        "--visualize",
        action="store_true",
        help="Open the spatial memory visualizer after the replay finishes.",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    source_root = Path(args.source_root)
    output_root = Path(args.output_root)
    ensure_roots_are_separate(source_root, output_root)

    run_dir = resolve_run(args.run, source_root)
    src = RunContext(run_dir=run_dir)
    if not src.replay.is_file() or src.replay.stat().st_size == 0:
        raise SystemExit(
            f"[ERROR] {src.replay} is missing or empty - nothing to replay."
        )
    if not src.telemetry.is_file():
        raise SystemExit(
            f"[ERROR] {src.telemetry} is missing. Body/emotion values come from telemetry; "
            "replaying without them would not be meaningful."
        )

    config_path = Path(args.config)
    if not config_path.is_file():
        raise SystemExit(f"[ERROR] config file not found: {config_path}")
    cfg = load_config(str(config_path))

    before = snapshot_tree(run_dir)
    out_dir = allocate_output_dir(output_root, run_dir.name, args.tag)
    dst = RunContext(run_dir=out_dir)

    print(f"Source run : {run_dir}")
    print(f"Output dir : {out_dir}")
    print(f"Config     : {config_path} (sha256:{sha256_prefix(config_path)})")

    warner = Warner()
    memory = build_memory_system(cfg.memory)
    memory.initialize_run_state(
        continuation=False,
        storage_path=str(dst.spatial_memory),
        episodes_dir=str(dst.episodes_dir),
    )
    # Safety: the archive must now live under the mirrored output folder.
    archive_root = Path(memory.episodic.archive.root).resolve()
    if archive_root != dst.episodes_dir.resolve():
        raise SystemExit(
            f"[ERROR] Episode archive points at {archive_root}, expected {dst.episodes_dir}. Aborting."
        )

    path_log: Optional[List[Vector2]] = [] if args.visualize else None
    stats, fidelity = run_replay(
        memory, cfg, src.replay, src.telemetry, args, warner, path_log
    )

    try:
        memory.shutdown_and_save(storage_path=str(dst.spatial_memory))
    except Exception as exc:
        stats.shutdown_error = repr(exc)
        traceback.print_exc()

    checks, notes = verify_artifacts(out_dir)

    after = snapshot_tree(run_dir)
    changes = [f"{k}: changed/removed" for k in before if after.get(k) != before[k]]
    changes += [f"{k}: newly created" for k in after if k not in before]
    source_unchanged = not changes

    result, code = decide_result(stats, fidelity, checks, source_unchanged)

    summary = {
        "source_run": str(run_dir),
        "output_dir": str(out_dir),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "config_path": str(config_path),
        "config_sha256_prefix": sha256_prefix(config_path),
        "body_alignment": args.body_alignment,
        "goal_skill_target": "not recorded - passed as None",
        "stats": stats.__dict__,
        "fidelity": fidelity.__dict__,
        "artifacts": [c.__dict__ for c in checks],
        "notes": notes,
        "source_unchanged": source_unchanged,
        "result": result,
    }
    try:
        with open(out_dir / SUMMARY_FILENAME, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
    except OSError as exc:
        print(f"[WARN] could not write {SUMMARY_FILENAME}: {exc}")

    print_summary(
        out_dir,
        run_dir,
        stats,
        fidelity,
        checks,
        notes,
        source_unchanged,
        changes,
        result,
    )
    if args.visualize:
        try:
            run_visualizer(memory.spatial_mem, path=path_log)
        except Exception as exc:
            print(f"[WARN] visualizer failed: {exc!r}")
    return code


if __name__ == "__main__":
    sys.exit(main())
