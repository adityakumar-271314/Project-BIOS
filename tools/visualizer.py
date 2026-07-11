"""
tools/visualizer.py

Post-mortem (or live) visualizer for core.memory.semantic.SemanticMemory.

Reads directly from a SemanticMemory instance — no JSON export needed.
Coordinate system matches Godot: +X right, +Y DOWN (we flip Y for screen).

Usage
-----
    from core.hippocampus import SemanticMemory
    from tools.visualizer import run_visualizer

    # After agent session ends (or any time):
    run_visualizer(agent.memory)

    # Or pass a recorded path list alongside the memory:
    run_visualizer(agent.memory, path=agent.memory_path_log)

Controls
--------
    Scroll / +/-     Zoom in / out
    Middle-drag      Pan
    H / F / L        Toggle hazard / food / landmark layers
    P                Toggle path
    R                Reset view to fit all data
    S                Save screenshot (bios_map_<timestamp>.png)
    ESC / Q          Quit
"""

from __future__ import annotations

import math
import sys
import os
import time
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pygame
from core.memory.semantic import SemanticMemory
from core.vector import Vector2

# ---------------------------------------------------------------------------
# Palette  (Godot-inspired dark UI)
# ---------------------------------------------------------------------------
BG = (15, 17, 21)
GRID_LINE = (30, 33, 40)
AXIS_COLOR = (55, 60, 75)
ORIGIN_DOT = (80, 85, 100)

HAZARD_BASE = (192, 57, 43)  # red
FOOD_BASE = (39, 174, 96)  # green
LM_COLOR = (155, 155, 165)  # grey
PATH_COLOR = (72, 140, 220)  # blue
AGENT_COLOR = (230, 230, 240)  # white-ish for death marker

TEXT_PRIMARY = (220, 220, 230)
TEXT_SECONDARY = (130, 130, 145)
TEXT_ACCENT = (100, 180, 255)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lerp_color(
    base: Tuple[int, int, int], t: float, dark=(15, 17, 21)
) -> Tuple[int, int, int]:
    """Blend base color toward background by (1-t) for intensity mapping."""
    t = max(0.0, min(1.0, t))
    return (
        int(dark[0] + (base[0] - dark[0]) * t),
        int(dark[1] + (base[1] - dark[1]) * t),
        int(dark[2] + (base[2] - dark[2]) * t),
    )


def _alpha_surf(
    color: Tuple[int, int, int], alpha: int, size: Tuple[int, int]
) -> pygame.Surface:
    s = pygame.Surface(size, pygame.SRCALPHA)
    s.fill((*color, alpha))
    return s


# ---------------------------------------------------------------------------
# Main visualizer
# ---------------------------------------------------------------------------


class _Visualizer:
    WIDTH = 1280
    HEIGHT = 800
    FONT_PATH = None  # uses pygame default

    def __init__(self, memory: SemanticMemory, path: Optional[List[Vector2]] = None):
        self.memory = memory
        self.path: List[Vector2] = path or []

        self.show_hazard = True
        self.show_food = True
        self.show_landmark = True
        self.show_path = True

        # View transform: screen = world * scale + (pan_x, pan_y)
        # NOTE: Y is FLIPPED to match screen space (Godot +Y = down = screen down)
        self._scale = 6.0  # pixels per world unit
        self._pan = pygame.math.Vector2(self.WIDTH / 2, self.HEIGHT / 2)

        self._dragging = False
        self._drag_start = pygame.math.Vector2()
        self._pan_start = pygame.math.Vector2()

        self._cell_size: float = memory._cell_size

    # ------------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------------

    def _w2s(self, wx: float, wy: float) -> Tuple[int, int]:
        # Internal memory space:
        # +X right
        # +Y up
        # Godot/screen space:
        # +X right
        # +Y down
        # Therefore flip Y before rendering.

        return (
            int(wx * self._scale + self._pan.x),
            int(-wy * self._scale + self._pan.y),
        )

    def _s2w(self, sx: float, sy: float) -> Tuple[float, float]:
        return (
            (sx - self._pan.x) / self._scale,
            -(sy - self._pan.y) / self._scale,
        )

    # ------------------------------------------------------------------
    # Fit all data on screen
    # ------------------------------------------------------------------

    def _fit_view(self) -> None:
        all_wx, all_wy = [], []

        for cx, cy in self.memory._grid.keys():
            all_wx.append(cx * self._cell_size)
            all_wy.append(cy * self._cell_size)

        for lm in self.memory._landmarks.values():
            all_wx.append(lm.pos.x)
            all_wy.append(lm.pos.y)

        for pt in self.path:
            all_wx.append(pt.x)
            all_wy.append(pt.y)

        if not all_wx:
            return

        min_x, max_x = min(all_wx), max(all_wx)
        min_y, max_y = min(all_wy), max(all_wy)
        span_x = max(max_x - min_x, self._cell_size * 4)
        span_y = max(max_y - min_y, self._cell_size * 4)

        pad = 0.85
        self._scale = min(
            self.WIDTH * pad / span_x,
            self.HEIGHT * pad / span_y,
        )
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        self._pan = pygame.math.Vector2(
            self.WIDTH / 2 - cx * self._scale,
            self.HEIGHT / 2 - cy * self._scale,
        )

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw_grid_lines(self, surf: pygame.Surface) -> None:
        """Lightly draw world-space grid lines for spatial reference."""
        cs = self._cell_size
        # visible world bounds
        wx0, wy0 = self._s2w(0, self.HEIGHT)
        wx1, wy1 = self._s2w(self.WIDTH, 0)

        min_wx, max_wx = min(wx0, wx1), max(wx0, wx1)
        min_wy, max_wy = min(wy0, wy1), max(wy0, wy1)

        start_cx = int(math.floor(min_wx / cs))
        end_cx = int(math.ceil(max_wx / cs))
        start_cy = int(math.floor(min_wy / cs))
        end_cy = int(math.ceil(max_wy / cs))

        for cx in range(start_cx, end_cx + 1):
            sx, _ = self._w2s(cx * cs, 0)
            pygame.draw.line(surf, GRID_LINE, (sx, 0), (sx, self.HEIGHT))
        for cy in range(start_cy, end_cy + 1):
            _, sy = self._w2s(0, cy * cs)
            pygame.draw.line(surf, GRID_LINE, (0, sy), (self.WIDTH, sy))

        # Axis lines
        ox, oy = self._w2s(0, 0)
        pygame.draw.line(surf, AXIS_COLOR, (ox, 0), (ox, self.HEIGHT), 1)
        pygame.draw.line(surf, AXIS_COLOR, (0, oy), (self.WIDTH, oy), 1)
        pygame.draw.circle(surf, ORIGIN_DOT, (ox, oy), 3)

    def _draw_cells(self, surf: pygame.Surface) -> None:
        cell_px = max(1, int(self._cell_size * self._scale))

        for (cx, cy), cell in self.memory._grid.items():
            wx = cx * self._cell_size
            wy = cy * self._cell_size
            sx, sy = self._w2s(wx, wy)

            # Quick cull
            if sx + cell_px < 0 or sx > self.WIDTH:
                continue
            if sy + cell_px < 0 or sy > self.HEIGHT:
                continue

            if self.show_hazard and cell.hazard > 0.01:
                color = _lerp_color(HAZARD_BASE, cell.hazard)
                alpha = int(40 + cell.hazard * 215)
                s = _alpha_surf(color, alpha, (cell_px, cell_px))
                surf.blit(s, (sx, sy))

            if self.show_food and cell.food > 0.01:
                color = _lerp_color(FOOD_BASE, cell.food)
                alpha = int(40 + cell.food * 215)
                s = _alpha_surf(color, alpha, (cell_px, cell_px))
                surf.blit(s, (sx, sy))

    def _draw_path(self, surf: pygame.Surface) -> None:
        if not self.show_path or len(self.path) < 2:
            return

        # Build screen points
        pts = [self._w2s(p.x, p.y) for p in self.path]

        # Draw as polyline segments (not circles!)
        pygame.draw.lines(
            surf, (*PATH_COLOR, 160), False, pts, max(1, int(self._scale * 0.1 + 0.5))
        )

        # Death/disconnect marker at final position
        ex, ey = pts[-1]
        r = max(4, int(self._scale * 0.35))
        pygame.draw.circle(surf, AGENT_COLOR, (ex, ey), r)
        pygame.draw.circle(surf, PATH_COLOR, (ex, ey), r, 1)

    def _draw_landmarks(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.show_landmark:
            return
        r = max(5, int(self._scale * 0.45))
        for lid, lm in self.memory._landmarks.items():
            sx, sy = self._w2s(lm.pos.x, lm.pos.y)
            pygame.draw.circle(surf, LM_COLOR, (sx, sy), r)
            pygame.draw.circle(surf, (200, 200, 210), (sx, sy), r, 1)
            if self._scale > 4:
                lbl = font.render(str(lid), True, (255, 255, 255))
                surf.blit(lbl, (sx - lbl.get_width() // 2, sy - lbl.get_height() // 2))

    def _draw_hud(
        self, surf: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font
    ) -> None:
        mem = self.memory
        grid_cells = len(mem._grid)
        lm_count = len(mem._landmarks)
        tick = mem._tick
        peak_hz = max((c.hazard for c in mem._grid.values()), default=0.0)
        peak_food = max((c.food for c in mem._grid.values()), default=0.0)

        lines = [
            ("tick", f"{tick}"),
            ("grid cells", f"{grid_cells}"),
            ("landmarks", f"{lm_count}"),
            ("peak hazard", f"{peak_hz:.2f}"),
            ("peak food", f"{peak_food:.2f}"),
            ("scale", f"{self._scale:.1f} px/u"),
        ]

        pad = 10
        line_h = 18
        panel_w = 180
        panel_h = pad * 2 + len(lines) * line_h + 4
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((15, 17, 21, 200))
        surf.blit(panel, (8, 8))

        for i, (label, value) in enumerate(lines):
            y = 8 + pad + i * line_h
            surf.blit(small_font.render(label, True, TEXT_SECONDARY), (14, y))
            surf.blit(small_font.render(value, True, TEXT_PRIMARY), (14 + 95, y))

        # Legend
        legend = [
            (HAZARD_BASE, "hazard", self.show_hazard),
            (FOOD_BASE, "food", self.show_food),
            (LM_COLOR, "landmark", self.show_landmark),
            (PATH_COLOR, "path", self.show_path),
        ]
        lx, ly = 8, self.HEIGHT - 10 - len(legend) * 20
        for color, label, active in legend:
            c = color if active else (50, 52, 60)
            pygame.draw.rect(surf, c, (lx, ly, 12, 12), border_radius=2)
            surf.blit(
                small_font.render(
                    label, True, TEXT_PRIMARY if active else TEXT_SECONDARY
                ),
                (lx + 18, ly - 1),
            )
            ly += 20

        # Controls hint
        hints = [
            "scroll: zoom",
            "drag: pan",
            "H/F/L/P: layers",
            "R: fit",
            "S: screenshot",
            "Q: quit",
        ]
        hx = self.WIDTH - 160
        hy = self.HEIGHT - len(hints) * 16 - 6
        for h in hints:
            surf.blit(small_font.render(h, True, TEXT_SECONDARY), (hx, hy))
            hy += 16

    # ------------------------------------------------------------------
    # Event loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        pygame.init()
        pygame.display.set_caption("BIOS — SemanticMemory Visualizer")
        surf = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        clock = pygame.time.Clock()

        font = pygame.font.SysFont("monospace", 11)
        small_font = pygame.font.SysFont("monospace", 11)

        self._fit_view()

        running = True
        while running:
            self.WIDTH, self.HEIGHT = surf.get_size()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_h:
                        self.show_hazard = not self.show_hazard
                    elif event.key == pygame.K_f:
                        self.show_food = not self.show_food
                    elif event.key == pygame.K_l:
                        self.show_landmark = not self.show_landmark
                    elif event.key == pygame.K_p:
                        self.show_path = not self.show_path
                    elif event.key == pygame.K_r:
                        self._fit_view()
                    elif event.key in (
                        pygame.K_PLUS,
                        pygame.K_EQUALS,
                        pygame.K_KP_PLUS,
                    ):
                        self._scale *= 1.2
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self._scale = max(0.2, self._scale / 1.2)
                    elif event.key == pygame.K_s:
                        fname = f"bios_map_{int(time.time())}.png"
                        pygame.image.save(surf, fname)
                        print(f"[visualizer] saved {fname}")

                elif event.type == pygame.MOUSEWHEEL:
                    mx, my = pygame.mouse.get_pos()
                    old_scale = self._scale
                    self._scale = max(
                        0.2, self._scale * (1.15 if event.y > 0 else 1 / 1.15)
                    )
                    ratio = self._scale / old_scale
                    self._pan.x = mx - (mx - self._pan.x) * ratio
                    self._pan.y = my - (my - self._pan.y) * ratio

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 2:
                        self._dragging = True
                        self._drag_start = pygame.math.Vector2(event.pos)
                        self._pan_start = pygame.math.Vector2(self._pan)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 2:
                        self._dragging = False

                elif event.type == pygame.MOUSEMOTION:
                    if self._dragging:
                        delta = pygame.math.Vector2(event.pos) - self._drag_start
                        self._pan = self._pan_start + delta

            # ---- Draw ------------------------------------------------
            surf.fill(BG)
            self._draw_grid_lines(surf)

            # Cells drawn onto an alpha surface so colours compose
            cell_layer = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            self._draw_cells(cell_layer)
            surf.blit(cell_layer, (0, 0))

            self._draw_path(surf)
            self._draw_landmarks(surf, font)
            self._draw_hud(surf, font, small_font)

            # Tooltip: hovered cell info
            mx, my = pygame.mouse.get_pos()
            wx, wy = self._s2w(mx, my)
            cs = self._cell_size
            hcx, hcy = int(math.floor(wx / cs)), int(math.floor(wy / cs))
            hcell = self.memory._grid.get((hcx, hcy))
            tip_lines = [f"cell ({hcx}, {hcy})", f"world ({wx:.1f}, {wy:.1f})"]
            if hcell:
                tip_lines += [
                    f"hazard {hcell.hazard:.3f}",
                    f"food   {hcell.food:.3f}",
                    f"tick   {hcell.last_updated_tick}",
                ]
            tw = max(len(l) for l in tip_lines) * 7 + 12
            th = len(tip_lines) * 15 + 8
            tip = pygame.Surface((tw, th), pygame.SRCALPHA)
            tip.fill((20, 22, 28, 220))
            for i, tl in enumerate(tip_lines):
                color = TEXT_ACCENT if i < 2 else TEXT_PRIMARY
                tip.blit(small_font.render(tl, True, color), (6, 4 + i * 15))
            surf.blit(
                tip,
                (min(mx + 14, self.WIDTH - tw - 4), min(my - 10, self.HEIGHT - th - 4)),
            )

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_visualizer(
    memory: SemanticMemory,
    path: Optional[List[Vector2]] = None,
) -> None:
    """
    Launch the visualizer window.

    Parameters
    ----------
    memory : SemanticMemory
        The hippocampus instance to inspect.  Can be called while the
        agent is still alive (reads current state) or post-mortem.
    path : list[Vector2] | None
        Optional ordered list of world-space positions representing the
        agent's dead-reckoning trail.  If your agent logs
        ``self.memory.internal_pos`` each tick, pass that list here.
        Without it the path layer is empty.
    """
    _Visualizer(memory, path).run()


# ---------------------------------------------------------------------------
# CLI: python -m tools.visualizer  (for quick smoke-test with dummy data)
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # Build a minimal fake config so SemanticMemory can be constructed
    class _Cfg:
        cell_size = 16.0
        landmark_alpha = 0.15
        grid_decay = 0.998
        stim_threshold = 0.05
        bias_radius = 80.0
        landmark_confidence_divisor = 10
        collision_velocity_damping = 0.3
        grid_prune_threshold = 0.005

    from core.memory.semantic import SemanticMemory, GridCell, LandmarkRecord

    mem = SemanticMemory(_Cfg())

    import random, math as _math

    rng = random.Random(7)
    path_log: List[Vector2] = []
    pos = Vector2(0, 0)
    vel = Vector2(0, 0)

    for t in range(600):
        # Spiral-ish movement
        angle = t * 0.07 + _math.sin(t * 0.04) * 1.5
        speed = 40 + _math.sin(t * 0.02) * 20
        vel = Vector2(_math.cos(angle) * speed, _math.sin(angle) * speed)
        pos = pos + vel * 0.05
        path_log.append(Vector2(pos.x, pos.y))

        cx = int(_math.floor(pos.x / 16))
        cy = int(_math.floor(pos.y / 16))
        key = (cx, cy)

        if (40 < pos.x < 120 and -20 < pos.y < 60) or pos.x < -50:
            v = rng.random() * 0.8
            if key not in mem._grid:
                mem._grid[key] = GridCell()
            mem._grid[key].hazard = min(
                1.0, mem._grid[key].hazard + v * (1 - mem._grid[key].hazard)
            )
            mem._grid[key].last_updated_tick = t
        if (-30 < pos.x < 30 and 40 < pos.y < 120) or pos.x > 100:
            v = rng.random() * 0.7
            if key not in mem._grid:
                mem._grid[key] = GridCell()
            mem._grid[key].food = min(
                1.0, mem._grid[key].food + v * (1 - mem._grid[key].food)
            )
            mem._grid[key].last_updated_tick = t
        if rng.random() > 0.97:
            lid = rng.randint(0, 4)
            mem._landmarks[lid] = LandmarkRecord(
                pos=Vector2(pos.x + rng.uniform(-8, 8), pos.y + rng.uniform(-8, 8)),
                last_seen_tick=t,
                observation_count=rng.randint(1, 20),
            )

    mem._tick = 600
    mem.internal_pos = pos

    run_visualizer(mem, path=path_log)
