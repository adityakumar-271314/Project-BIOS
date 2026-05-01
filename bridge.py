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
    # Use makefile for easier line-by-line reading
    client_file = conn.makefile('rw', encoding='utf-8')
    agent = Agent()

    try:
        while True:
            line = client_file.readline()
            if not line: break
            
            try:
                world_data = json.loads(line) 
                # Consolidate data parsing here
                sensors = {
                    "ray_c": float(world_data.get("ray_c", 1.0)),
                    "ray_l": float(world_data.get("ray_l", 1.0)),
                    "ray_r": float(world_data.get("ray_r", 1.0)),
                    "current_rotation": float(world_data.get("current_rotation", 0.0)),
                    "is_stuck": bool(world_data.get("is_stuck", False)),
                    "sensed_objects": world_data.get("sensed_objects", []),
                    "hazard": float(world_data.get("hazard", 0.0)),
                    "food_stimulus": float(world_data.get("food_stimulus", 0.0))
                }
            except Exception as e:
                print(f"BRIDGE ERROR: {e}")
                # Complete fallback dictionary to prevent KeyError/NameError
                sensors = {
                    "ray_c": 1.0, "ray_l": 1.0, "ray_r": 1.0, 
                    "hazard": 0.0, "food_stimulus": 0.0, "sensed_objects": [],
                    "current_rotation": 0.0, "is_stuck": False
                }

            motor_output = agent.tick(
                env_damage=sensors["hazard"],
                food=sensors["food_stimulus"],
                sensor_data=sensors
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
                "alive": agent.bst.is_alive
            }

            client_file.write(json.dumps(response) + "\n")
            client_file.flush()
            
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        conn.close()
        server.close()

if __name__ == "__main__":
    run_brain_server()
