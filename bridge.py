import socket
import json
from core.agent import Agent  

def run_brain_server():
    host = "127.0.0.1"
    port = 9999
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    
    print(f"BIOS Brain Server active on {host}:{port}. Waiting for Godot...")
    
    conn, addr = server.accept()
    client_file = conn.makefile('rw', encoding='utf-8')
    agent = Agent()

    try:
        while True:
            line = client_file.readline()
            if not line: break
            
            world_data = json.loads(line)
            agent.tick(
                env_damage=world_data.get("hazard", 0),
                food=world_data.get("food", 0)
            )
            
            response = {
                "action": agent.current_action, 
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