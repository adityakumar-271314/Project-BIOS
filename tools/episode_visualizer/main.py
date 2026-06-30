import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from tools.episode_visualizer.controller import VisualizerController
from core.memory.storage.browser import EpisodeBrowser
from tools.episode_visualizer.controller import VisualizerController
from tools.episode_visualizer.replay_loader import load_from_storage

def main():
    browser = EpisodeBrowser()
    episodes = browser.list()
    
    if not episodes:
        print("[Visualizer Interruption] No recorded simulation directories discovered.")
        return

    print("\n=== SYSTEM EPISODE BROWSER ===")
    for idx, path in enumerate(episodes):
        print(f"[{idx}] {path.name}")
        
    try:
        selection = int(input("\nEnter index to initiate live visualization reconstruction: "))
        selected_path = episodes[selection]
        
        # Build session via active reconstruction interface
        session = load_from_storage(selected_path)
        
        controller = VisualizerController()
        controller.load_session(session)
        controller.run()
    except Exception as e:
        print(f"\n[Fatal Pipeline Interruption] Verification system halted: {e}")

if __name__ == "__main__":
    main()