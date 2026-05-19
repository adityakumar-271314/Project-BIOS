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


import math
import socket
import json
from core.agent import Agent
from core.config_loader import load_config
from core.constants import SPAWN_OFFSET_X, SPAWN_OFFSET_Y, DRIFT_WARNING_THRESHOLD
from core.data_models import SensorPacket
from tools.visualizer import run_visualizer
from core.telemetry import (
    TelemetryRecorder,
    TickTelemetry,
)
from core.replay import (
    ReplayRecorder,
    ReplayFrame,
)


def run_brain_server():
    host = "127.0.0.1"
    port = 9999
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()

    print(f"BIOS Brain Server active on {host}:{port}. Waiting for Godot...")

    conn, addr = server.accept()
    client_file = conn.makefile("rw", encoding="utf-8")
    cfg = load_config()
    init_packet = {
    "type": "INIT",
    "world_seed": cfg.simulation.world_seed,
}
    client_file.write(json.dumps(init_packet) + "\n")
    client_file.flush()
    agent = Agent()
    telemetry = TelemetryRecorder()
    replay = ReplayRecorder()
    cfg = load_config()
    path_log = []
    DEBUG = False # Set to True to enable detailed debug output each tick\
    try:
        while True:
            line = client_file.readline()
            if not line:
                break

            try:
                world_data = json.loads(line)
                sensors = SensorPacket.from_world_data(world_data)

            except Exception as e:
                print(f"BRIDGE ERROR: {e}")
                # Complete fallback dictionary to prevent KeyError/NameError
                sensors = SensorPacket(is_real_data=False)

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
                    grid_cells=len(agent.memory.semantic._grid),
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
                "current_goal": agent.brain.gsm.active_goal.name if agent.brain.gsm.active_goal else "Wander",
                "landmark_count": len(agent.memory.landmarks),
                "grid_cells": len(agent.memory.semantic._grid),
                "episodic_memories": agent.memory.get_debug_memories(),
            }

            client_file.write(json.dumps(response) + "\n")
            client_file.flush()

            # --- DEBUGGING BLOCK ---
            if DEBUG:
                real_pos_x = sensors.real_pos_x
                real_pos_y = sensors.real_pos_y

                # 1. Get the raw mental coordinates
                internal = agent.memory.semantic.internal_pos

                # 2. Transform Mental -> Godot Space
                # We add the spawn offset and invert the Y axis
                mental_in_godot_x = internal.x + SPAWN_OFFSET_X
                mental_in_godot_y = SPAWN_OFFSET_Y - internal.y

                # 3. Calculate "Drift" (Distance between reality and imagination)
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
                    f"MEMORY STATS:    Cells: {len(agent.memory.semantic._grid)} | Landmarks: {len(agent.memory.semantic._landmarks)}"
                )

                if drift_distance > DRIFT_WARNING_THRESHOLD:
                    print("WARNING: Agent is experiencing high spatial drift!")
                print("-" * 50)

    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        telemetry.close()
        replay.close()
        conn.close()
        server.close()
        run_visualizer(agent.memory.semantic, path=path_log)


if __name__ == "__main__":       
    run_brain_server()