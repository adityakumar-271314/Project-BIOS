import math
import socket
import json
from core.agent import Agent
from core.constants import (
    SPAWN_OFFSET_X, 
    SPAWN_OFFSET_Y, 
    DRIFT_WARNING_THRESHOLD
)
from core.data_models import (
    SensorPacket,
)
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
    agent = Agent()
    telemetry = TelemetryRecorder()
    replay = ReplayRecorder()
    DEBUG = False  # Set to True to enable detailed debug output each tick
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
                    grid_cells=len(agent.memory._grid),
                )
            )

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
                "alive": agent.bst.is_alive,
            }

            client_file.write(json.dumps(response) + "\n")
            client_file.flush()

            # --- DEBUGGING BLOCK ---
            if DEBUG:
                real_pos_x = sensors.real_pos_x
                real_pos_y = sensors.real_pos_y

                # 1. Get the raw mental coordinates
                internal = agent.memory.internal_pos

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
                    f"MEMORY STATS:    Cells: {len(agent.memory._grid)} | Landmarks: {len(agent.memory._landmarks)}"
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


if __name__ == "__main__":
    run_brain_server()
