# FILE: tools/episode_visualizer/presenters/package_assembler.py
from typing import Dict, List, Optional

from core.memory.schemas import (
    EpisodeHierarchy,
    EpisodeNode,
    EpisodicEvent,
    HierarchyLevel,
    ReconstructedTick,
)
from tools.episode_visualizer.presenters.debug_presenter import DebugPresenter
from tools.episode_visualizer.presenters.flow_presenter import FlowPresenter
from tools.episode_visualizer.presenters.hierarchy_presenter import (
    HierarchyPresenter,
)
from tools.episode_visualizer.presenters.schemas import PresentationPackage
from tools.episode_visualizer.presenters.timeline_presenter import (
    TimelinePresenter,
)


class PresentationPackageAssembler:
    """
    Main orchestration service for the presentation layer.
    Assembles a complete, immutable PresentationPackage from an EpisodicEvent
    and optional supplementary memory structures.
    """

    @staticmethod
    def assemble(
        event: EpisodicEvent,
        reconstructed_ticks: Optional[List[ReconstructedTick]] = None,
        hierarchy: Optional[EpisodeHierarchy] = None,
        nodes_map: Optional[Dict[str, EpisodeNode]] = None,
        include_debug: bool = True,
    ) -> PresentationPackage:
        """
        Builds and returns a unified PresentationPackage.

        Args:
            event: The target EpisodicEvent to visualize.
            reconstructed_ticks: Optional high-resolution tick telemetry.
            hierarchy: Optional structural hierarchy tree for the episode.
            nodes_map: Optional full node graph dictionary.
            include_debug: Flag indicating whether to attach diagnostic HUD data.

        Returns:
            An immutable PresentationPackage ready for rendering.
        """
        # 1. Timeline View
        timeline = TimelinePresenter.present(
            event=event,
            reconstructed_ticks=reconstructed_ticks,
        )

        # 2. Behavioral Flow View
        flow = FlowPresenter.present(event=event)

        # 3. Hierarchy Graph View (if hierarchy data is available)
        event_id = getattr(event, "event_id", getattr(event, "id", "unknown_event"))

        # 3. Hierarchy Graph View (if hierarchy data is available)
        hierarchy_view = None
        if hierarchy or nodes_map:
            # If hierarchy object isn't provided but nodes_map is, synthesize a stub hierarchy
            if not hierarchy and nodes_map:
                dummy_root = list(nodes_map.keys())[0] if nodes_map else event_id
                hierarchy = EpisodeHierarchy(
                    hierarchy_id=dummy_root,
                    root_id=event_id,
                    episode_ids=(event_id,),
                    level=HierarchyLevel("episode"),
                )

            if hierarchy:
                hierarchy_view = HierarchyPresenter.present(
                    hierarchy=hierarchy,
                    nodes_map=nodes_map,
                )

            if hierarchy:
                hierarchy_view = HierarchyPresenter.present(
                    hierarchy=hierarchy,
                    nodes_map=nodes_map,
                )

        # 4. Diagnostic Debug View
        debug_view = None
        if include_debug:
            debug_view = DebugPresenter.present(
                event=event,
                reconstructed_ticks=reconstructed_ticks,
            )

        return PresentationPackage(
            item_id=event_id,
            timeline=timeline,
            flow=flow,
            hierarchy=hierarchy_view,
            debug=debug_view,
        )
