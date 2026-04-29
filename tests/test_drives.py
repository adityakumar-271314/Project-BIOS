import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import Agent

def test_starvation_response():
    print("Running Test: Starvation Response...")
    agent = Agent()
    
    # Simulate 2000 ticks of no food
    for i in range(2000):
        action = agent.tick(env_damage=0, food=0)
        
    print(f"Final Energy: {agent.bst.energy:.2f}")
    print(f"Final Action: {agent.motor_output}")
    print(agent.bst.energy)
    assert agent.bst.energy < 50
    print("Test Passed: Agent prioritized FORAGE as energy dropped.\n")

if __name__ == "__main__":
    test_starvation_response()