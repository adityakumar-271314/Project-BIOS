"""
TCP Bridge between Godot Simulation and Python Cognition Engine.

This module acts as the communication gateway:
- Starts a TCP server on 127.0.0.1:9999
- Performs initial handshake with world seed
- Receives sensor data from Godot each physics tick
- Forwards processed data to the Agent
- Sends motor commands (thrust, steer) back to Godot
- Records telemetry and replay data
- Launches the spatial memory visualizer when the agent dies or connection closes

Key responsibilities:
    - JSON serialization/deserialization
    - Robust error handling and fallback SensorPacket
    - Lifecycle management of Agent, TelemetryRecorder, and ReplayRecorder
"""

"""
TCP Bridge between Godot Simulation and Python Cognition Engine.
"""
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import math
import socket
import json
from core.agent import Agent
from infra.config_loader import load_config
from infra.constants import SPAWN_OFFSET_X, SPAWN_OFFSET_Y, DRIFT_WARNING_THRESHOLD
from infra.data_models import SensorPacket
from infra.agent_state import AgentState
from infra.world_state import WorldState
from infra.run_manager import setup_run_session, load_world_state, RunContext
from tools.visualizer import run_visualizer
from infra.json import BIOSJsonEncoder
from infra.telemetry import (
    TelemetryRecorder,
    TickTelemetry,
)
from infra.replay import (
    ReplayRecorder,
    ReplayFrame,
)
import traceback


def get_new_minimized_memories(agent, tracker_state={"last_sent_index": 0}):
    """
    Slices newly formed memories since the last sync tick and strips them
    down to the bare minimum fields to eliminate network choking.
    """
    all_memories = agent.memory.get_debug_memories()
    total_memories = len(all_memories)
    new_minimized = []

    if total_memories > tracker_state["last_sent_index"]:
        for i in range(tracker_state["last_sent_index"], total_memories):
            mem = all_memories[i]

            # Structural map matching metadata_index field constraints
            minimized_packet = {
                "peak_tick": mem.get("peak_tick"),
                "event_type": mem.get("event_type"),
                "peak_significance": mem.get("peak_significance"),
                "peak_x": mem.get("peak_x"),
                "peak_y": mem.get("peak_y"),
            }
            new_minimized.append(minimized_packet)

        tracker_state["last_sent_index"] = total_memories

    return new_minimized


def run_brain_server():
    host = "127.0.0.1"
    port = 9999
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()

    cfg = load_config()
    ctx = setup_run_session()  # Returns RunContext instance
    world_state = load_world_state(ctx, cfg.simulation.world_seed)

    print(
        f"BIOS Brain Server active on {host}:{port}. Session directory: {ctx.run_dir}"
    )

    conn, addr = server.accept()
    client_file = conn.makefile("rw", encoding="utf-8")

    is_continuation = world_state.continuation
    agent = Agent()

    telemetry = TelemetryRecorder(path=str(ctx.telemetry))
    replay = ReplayRecorder(path=str(ctx.replay))
    path_log = []
    eaten_food_ids = []

    if is_continuation:
        agent.memory.initialize_run_state(
            continuation=True,
            storage_path=str(ctx.spatial_memory),
            episodes_dir=str(ctx.episodes_dir),
        )
        agent.import_state(world_state.agent_state)

        if ctx.world_state.exists():
            with open(ctx.world_state, "r") as f:
                world_state_data = json.load(f)
                eaten_food_ids = world_state_data.get("eaten_food_ids", [])
    else:
        agent.memory.reset_state(
            storage_path=str(ctx.spatial_memory), episodes_dir=str(ctx.episodes_dir)
        )

    # Include eaten_food_ids in the INIT packet
    init_packet = {
        "type": "INIT",
        "world_seed": world_state.world_seed,
        "continuation": world_state.continuation,
        "consumed_food_ids": world_state.consumed_food_ids,
        "agent_state": (
            world_state.agent_state.__dict__ if world_state.agent_state else None
        ),
    }
    latest_consumed_food_ids = eaten_food_ids
    client_file.write(json.dumps(init_packet) + "\n")
    client_file.flush()
    DEBUG = False  # Set to True to enable detailed debug output each tick
    try:
        while True:

            line = client_file.readline()
            if not line:
                print("BRIDGE: EOF received from Godot. Client disconnected.")
                break

            try:
                world_data = json.loads(line)
                sensors = SensorPacket.from_world_data(world_data)
            except Exception as e:
                print(f"BRIDGE ERROR: {e}")
                sensors = SensorPacket(is_real_data=False)

            if "consumed_food_ids" in world_data:
                latest_consumed_food_ids = world_data["consumed_food_ids"]
            # To capture it if sent from AgentBody via standard sensor payload:
            elif hasattr(sensors, "consumed_food_ids"):
                latest_consumed_food_ids = sensors.consumed_food_ids

            motor_output = agent.tick(
                env_damage=sensors.hazard_stim,
                food=sensors.food_stim,
                sensor_data=sensors,
                delta=sensors.delta,
            )

            telemetry.record(
                TickTelemetry(
                    tick=agent.tick_count,
                    energy=agent.bst.energy,
                    integrity=agent.bst.integrity,
                    stress=agent.ehe.stress,
                    fear=agent.ehe.fear,
                    drive=agent.ehe.drive,
                    thrust=motor_output.thrust,
                    steer=motor_output.steer,
                    pos_x=agent.memory.internal_pos.x,
                    pos_y=agent.memory.internal_pos.y,
                    velocity_x=agent.memory.internal_vel.x,
                    velocity_y=agent.memory.internal_vel.y,
                    landmark_count=len(agent.memory.landmarks),
                    grid_cells=len(agent.memory.spatial_mem._grid),
                )
            )
            path_log.append(agent.memory.internal_pos.copy())

            replay.record(
                ReplayFrame(
                    tick=agent.tick_count,
                    sensor_packet=sensors.to_dict(),
                    motor_output=motor_output.to_dict(),
                )
            )

            if not agent.bst.is_alive:
                response = {"action": "DECEASED", "alive": False}
                client_file.write(json.dumps(response) + "\n")
                client_file.flush()
                print(f"Agent Died")
                break

            response = {
                "thrust": motor_output.thrust,
                "steer": motor_output.steer,
                "energy": agent.bst.energy,
                "integrity": agent.bst.integrity,
                "stress": agent.ehe.stress,
                "fear": agent.ehe.fear,
                "drive": agent.ehe.drive,
                "alive": agent.bst.is_alive,
                "current_goal": (
                    agent.brain.gsm.active_goal.name
                    if agent.brain.gsm.active_goal
                    else "Wander"
                ),
                "landmark_count": len(agent.memory.landmarks),
                "grid_cells": len(agent.memory.spatial_mem._grid),
                "new_memories": get_new_minimized_memories(agent),
            }

            client_file.write(json.dumps(response, cls=BIOSJsonEncoder) + "\n")
            client_file.flush()

            # --- DEBUGGING BLOCK ---
            if DEBUG:
                real_pos_x = sensors.real_pos_x
                real_pos_y = sensors.real_pos_y
                internal = agent.memory.spatial_mem.internal_pos
                mental_in_godot_x = internal.x + SPAWN_OFFSET_X
                mental_in_godot_y = SPAWN_OFFSET_Y - internal.y
                error_x = real_pos_x - mental_in_godot_x
                error_y = real_pos_y - mental_in_godot_y
                drift_distance = math.sqrt(error_x**2 + error_y**2)

                print("-" * 50)
                print(f"REAL POSITION:   ({real_pos_x:.1f}, {real_pos_y:.1f})")
                print(
                    f"MENTAL ESTIMATE: ({mental_in_godot_x:.1f}, {mental_in_godot_y:.1f})"
                )
                print(f"DRIFT ERROR:     {drift_distance:.2f} pixels")
                print(
                    f"MEMORY STATS:    Cells: {len(agent.memory.spatial_mem._grid)} | Landmarks: {len(agent.memory.spatial_mem._landmarks)}"
                )

                if drift_distance > DRIFT_WARNING_THRESHOLD:
                    print("WARNING: Agent is experiencing high spatial drift!")
                print("-" * 50)

    except Exception as e:
        print(f"BRIDGE FATAL EXIT: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()

    finally:
        final_agent_state = AgentState.from_agent(agent)

        if "sensors" in locals() and sensors.is_real_data:
            final_agent_state.internal_pos_x = sensors.real_pos_x
            final_agent_state.internal_pos_y = sensors.real_pos_y
            if hasattr(sensors, "current_rotation"):
                final_agent_state.rotation = sensors.current_rotation

        final_world_state = WorldState(
            run_id=world_state.run_id,
            world_seed=world_state.world_seed,
            continuation=True,
            consumed_food_ids=latest_consumed_food_ids,
            agent_state=final_agent_state,
        )

        # Save state files cleanly via ctx properties
        final_world_state.save(ctx.world_state)
        agent.memory.shutdown_and_save(storage_path=str(ctx.spatial_memory))

        telemetry.close()
        replay.close()
        conn.close()
        server.close()
        run_visualizer(agent.memory.spatial_mem, path=path_log)


if __name__ == "__main__":
    run_brain_server()
