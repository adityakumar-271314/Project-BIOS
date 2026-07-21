import sys
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from tools.episode_visualizer.controller import VisualizerController


def main():
    controller = VisualizerController()
    controller.run()


if __name__ == "__main__":
    main()