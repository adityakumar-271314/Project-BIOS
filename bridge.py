import math
import socket
import json
from core.agent import Agent

# TODO: Refactor sensory data pipeline. Currently mixing float/dict types across modules.


def run_brain_server():
    host = "127.0.0.1"
    port = 9999
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)

    print(f"BIOS Brain Server active on {host}:{port}. Waiting for Godot...")

    conn, addr = server.accept()
    client_file = conn.makefile("rw", encoding="utf-8")
    agent = Agent()
    DEBUG = False  # Set to True to enable detailed debug output each tick
    try:
        while True:
            line = client_file.readline()
            if not line:
                break

            try:
                world_data = json.loads(line)
                sensors = {
                    "is_real_data": True,
                    "delta": float(world_data.get("delta", 0.016)),
                    "accel": world_data.get("accel", {"x": 0.0, "y": 0.0}),
                    "ray_c": float(world_data.get("ray_c", 1.0)),
                    "ray_l": float(world_data.get("ray_l", 1.0)),
                    "ray_r": float(world_data.get("ray_r", 1.0)),
                    "current_rotation": float(world_data.get("current_rotation", 0.0)),
                    "is_stuck": bool(world_data.get("is_stuck", False)),
                    "sensed_objects": world_data.get("sensed_objects", []),
                    "hazard_stim": float(world_data.get("hazard_stim", 0.0)),
                    "food_stim": float(world_data.get("food_stim", 0.0)),
                    "collision_normals": world_data.get("collision_normals", []),
                    "real_pos_x": float(world_data.get("global_x", 0.0)),
                    "real_pos_y": float(world_data.get("global_y", 0.0)),
                }

                # Invert (godot) Y axis for consistency with internal coordinate system
                raw_normals = world_data.get("collision_normals", [])
                formatted_normals = []
                for n in raw_normals:
                    nx = float(n.get("x", 0.0))
                    ny = float(n.get("y", 0.0))
                    formatted_normals.append({"x": -nx, "y": -ny})
                    sensors["collision_normals"] = formatted_normals
                sensors["accel"]["y"] = -world_data.get("accel", {}).get("y", 0.0)
                sensors["current_rotation"] = -float(
                    world_data.get("current_rotation", 0.0)
                )
                for obj in sensors["sensed_objects"]:
                    obj["angle"] = -obj["angle"]

            except Exception as e:
                print(f"BRIDGE ERROR: {e}")
                # Complete fallback dictionary to prevent KeyError/NameError
                sensors = {
                    "is_real_data": False,
                    "delta": 0.016,
                    "accel": {"x": 0.0, "y": 0.0},
                    "ray_c": 1.0,
                    "ray_l": 1.0,
                    "ray_r": 1.0,
                    "hazard_stim": 0.0,
                    "food_stim": 0.0,
                    "sensed_objects": [],
                    "collision_normals": [],
                    "current_rotation": 0.0,
                    "is_stuck": False,
                }
            motor_output = agent.tick(
                env_damage=sensors["hazard_stim"],
                food=sensors["food_stim"],
                sensor_data=sensors,
                delta=sensors["delta"],
            )

            if not agent.bst.is_alive:
                response = {"action": "DECEASED", "alive": False}
                client_file.write(json.dumps(response) + "\n")
                client_file.flush()
                break

            response = {
                "thrust": motor_output.get("thrust", 0.0),
                "steer": motor_output.get("steer", 0.0),
                "energy": agent.bst.energy,
                "integrity": agent.bst.integrity,
                "stress": agent.ehe.stress,
                "alive": agent.bst.is_alive,
            }

            client_file.write(json.dumps(response) + "\n")
            client_file.flush()

            # --- DEBUGGING BLOCK ---
            if DEBUG:
                real_pos_x = sensors.get("real_pos_x", 576.0)
                real_pos_y = sensors.get("real_pos_y", 324.0)

                # 1. Get the raw mental coordinates
                internal = agent.memory.internal_pos

                # 2. Transform Mental -> Godot Space
                # We add the spawn offset and invert the Y axis
                mental_in_godot_x = internal.x + 576.0
                mental_in_godot_y = 324.0 - internal.y

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
                    f"MEMORY STATS:    Cells: {len(agent.memory._grid)} | Landmarks: {len(agent.memory._landmarks)}"
                )

                if drift_distance > 50:
                    print("WARNING: Agent is experiencing high spatial drift!")
                print("-" * 50)

    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        conn.close()
        server.close()


if __name__ == "__main__":
    run_brain_server()
