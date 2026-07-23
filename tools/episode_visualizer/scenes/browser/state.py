# tools/episode_visualizer/scenes/browser/state.py


class BrowserState:
    """Encapsulates all search, filtering, selection, and view toggles for the browser."""

    def __init__(self):
        self.search_query = ""
        self.search_active = False
        self.show_filters = True
        self.dragging_slider = None  # 'sig', 'tick_start', 'tick_end'

        # Two-level navigation hierarchy state
        self.current_view = "RUNS"  # 'RUNS' or 'EPISODES'
        self.selected_run_path = None
        self.selected_run_name = None

        # Filter parameters
        self.event_types = [
            "damage_spike",
            "food_recovery",
            "hazard_encounter",
            "danger_state",
            "starvation_state",
            "high_significance",
        ]
        self.active_event_filter = None
        self.min_peak_significance = 0
        self.episode_id_filter = ""

        # Ticks repository bounds & handles
        self.min_repository_ticks = 0
        self.max_repository_ticks = 2000
        self.tick_start = 0
        self.tick_end = 2000

        # Selection index & preview metadata
        self.selected_idx = 0
        self.selected_metadata = {}

    def reset_filters(self):
        self.active_event_filter = None
        self.min_peak_significance = 0
        self.episode_id_filter = ""
        self.tick_start = self.min_repository_ticks
        self.tick_end = self.max_repository_ticks
        self.search_query = ""
