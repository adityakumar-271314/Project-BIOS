# FILE: tools/episode_visualizer/presenters/flow_presenter.py
from typing import List, Tuple

from core.memory.schemas import BehavioralTransition, EpisodicEvent
from tools.episode_visualizer.presenters.schemas import (
    BehaviorFlow,
    TransitionEdge,
    TransitionNode,
)


class FlowPresenter:
    """
    Pure presenter component that transforms EpisodeSignature behavioral transitions
    into a structured BehaviorFlow representation for visualization.
    """

    @staticmethod
    def present(event: EpisodicEvent) -> BehaviorFlow:
        sig = event.signature

        nodes: List[TransitionNode] = []
        edges: List[TransitionEdge] = []

        # Process transitions across all three behavioral categories
        FlowPresenter._process_category_transitions(
            transitions=sig.goal_transitions,
            category="goal",
            start_tick=event.start_tick,
            end_tick=event.end_tick,
            nodes=nodes,
            edges=edges,
        )

        FlowPresenter._process_category_transitions(
            transitions=sig.skill_transitions,
            category="skill",
            start_tick=event.start_tick,
            end_tick=event.end_tick,
            nodes=nodes,
            edges=edges,
        )

        FlowPresenter._process_category_transitions(
            transitions=sig.target_transitions,
            category="target",
            start_tick=event.start_tick,
            end_tick=event.end_tick,
            nodes=nodes,
            edges=edges,
        )

        # Sort nodes chronologically by tick, then by category
        nodes.sort(key=lambda n: (n.tick, n.state_category))
        edges.sort(key=lambda e: (e.from_tick, e.to_tick, e.state_category))

        return BehaviorFlow(
            dominant_goal=sig.dominant_goal,
            dominant_skill=sig.dominant_skill,
            dominant_target=sig.dominant_target,
            outcome_completed=sig.outcome_completed,
            nodes=tuple(nodes),
            edges=tuple(edges),
        )

    @staticmethod
    def _process_category_transitions(
        transitions: Tuple[BehavioralTransition, ...],
        category: str,
        start_tick: int,
        end_tick: int,
        nodes: List[TransitionNode],
        edges: List[TransitionEdge],
    ) -> None:
        if not transitions:
            return

        # Map initial transition state at transition tick
        for i, t in enumerate(transitions):
            # Create origin node if this is the first transition
            if i == 0 and t.from_state is not None:
                nodes.append(
                    TransitionNode(
                        tick=start_tick,
                        state_category=category,
                        state_value=t.from_state,
                    )
                )

            # Destination node for current transition
            nodes.append(
                TransitionNode(
                    tick=t.tick,
                    state_category=category,
                    state_value=t.to_state,
                )
            )

            # Directed transition edge
            from_t = start_tick if i == 0 else transitions[i - 1].tick
            edges.append(
                TransitionEdge(
                    from_tick=from_t,
                    to_tick=t.tick,
                    state_category=category,
                    from_state=t.from_state,
                    to_state=t.to_state,
                )
            )
