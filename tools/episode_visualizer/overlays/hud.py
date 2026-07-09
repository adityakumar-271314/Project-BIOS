import pygame
from tools.episode_visualizer.config import (
    BLACK, WHITE, PANEL_BG, PANEL_BORDER, 
    RED, GREEN, BLUE, YELLOW, ORANGE
)

class HUDOverlay:
    def __init__(self):
        # Increased baseline sizes substantially for immediate legibility
        self.visible = True
        self.font_sm = pygame.font.SysFont(None, 18)
        self.font_md = pygame.font.SysFont(None, 22)
        self.font_lg = pygame.font.SysFont(None, 32)

    def render(self, screen, session, playback, camera, ui=None):

        if not self.visible or not session or not playback:
            return

        tick = playback.get_current_tick()
        if not tick:
            return

        screen_w, screen_h = screen.get_size()
        
        if ui:
            self.font_sm = pygame.font.SysFont(None, ui.r(18))
            self.font_md = pygame.font.SysFont(None, ui.r(22))
            self.font_lg = pygame.font.SysFont(None, ui.r(32))

        # 1. TOP LEFT: SESSION CONTEXT
        self._render_header(screen, session, playback, tick, ui)

        # 2. RIGHT BAR: COGNITIVE SIDEBAR
        self._render_sidebar(screen, tick, screen_w, ui)

    def _render_header(self, screen, session, playback, tick, ui):
        hx = ui.x(20) if ui else 20
        hy = ui.y(20) if ui else 20
        
        title_txt = self.font_lg.render(session.name.upper(), True, BLACK)
        screen.blit(title_txt, (hx, hy))
        
        meta_y = hy + (ui.y(32) if ui else 32)
        frame_str = f"FRAME: {playback.current_frame} / {playback.total_frames - 1}   |   TICK: {tick.tick}   |   SPEED: {playback.speed:.1f}x"
        frame_txt = self.font_md.render(frame_str, True, (60, 60, 60))
        screen.blit(frame_txt, (hx, meta_y))

    def _render_sidebar(self, screen, tick, screen_w, ui):
        sb_w = ui.w(280) if ui else 280  # Widened container for comfortable value reads
        sb_x = screen_w - sb_w - (ui.x(20) if ui else 20)
        sb_y = ui.y(20) if ui else 20
        
        row_h = ui.y(24) if ui else 24
        pad = ui.r(14) if ui else 14
        inner_w = sb_w - (pad * 2)

        # Expanded total_h calculation guarantees all metrics remain entirely nested within the bounds
        total_h = ui.h(335) if ui else 335
        pygame.draw.rect(screen, PANEL_BG, (sb_x, sb_y, sb_w, total_h), 0, ui.r(6) if ui else 6)
        pygame.draw.rect(screen, PANEL_BORDER, (sb_x, sb_y, sb_w, total_h), ui.w(2) if ui else 2, ui.r(6) if ui else 6)

        curr_y = sb_y + pad

        # SECTION A: RECONSTRUCTION TRUST
        trust_lbl = self.font_md.render("RECONSTRUCTION ACCURACY", True, WHITE)
        screen.blit(trust_lbl, (sb_x + pad, curr_y))
        curr_y += row_h + ui.y(4)

        conf_color = GREEN if tick.confidence >= 0.9 else (ORANGE if tick.confidence >= 0.6 else RED)
        self._render_bar(screen, sb_x + pad, curr_y, inner_w, ui.h(10) if ui else 10, tick.confidence, conf_color, ui)
        curr_y += ui.y(14) if ui else 14

        drift_str = f"Drift Vector: {tick.drift:.4f} units"
        drift_color = WHITE if tick.drift <= 0.1 else RED
        drift_txt = self.font_sm.render(drift_str, True, drift_color)
        screen.blit(drift_txt, (sb_x + pad, curr_y))
        
        curr_y += row_h
        pygame.draw.line(screen, (55, 65, 90), (sb_x + pad, curr_y), (sb_x + sb_w - pad, curr_y), ui.w(1) if ui else 1)
        curr_y += ui.y(12) if ui else 12

        # SECTION B: THREAT SPECTRUM
        threat_lbl = self.font_md.render("THREAT SPECTRUM", True, WHITE)
        screen.blit(threat_lbl, (sb_x + pad, curr_y))
        curr_y += row_h + ui.y(4)

        curr_y = self._render_labeled_bar(screen, "FEAR", tick.fear, RED, sb_x + pad, curr_y, inner_w, row_h, ui)
        curr_y = self._render_labeled_bar(screen, "STRESS", tick.stress, ORANGE, sb_x + pad, curr_y, inner_w, row_h, ui)
        
        pygame.draw.line(screen, (55, 65, 90), (sb_x + pad, curr_y), (sb_x + sb_w - pad, curr_y), ui.w(1) if ui else 1)
        curr_y += ui.y(12) if ui else 12

        # SECTION C: MOTIVATION VECTOR
        mot_lbl = self.font_md.render("MOTIVATION VECTOR", True, WHITE)
        screen.blit(mot_lbl, (sb_x + pad, curr_y))
        curr_y += row_h + ui.y(4)

        curr_y = self._render_labeled_bar(screen, "DRIVE", tick.drive, BLUE, sb_x + pad, curr_y, inner_w, row_h, ui)
        curr_y = self._render_labeled_bar(screen, "ENERGY", tick.energy, GREEN, sb_x + pad, curr_y, inner_w, row_h, ui)
        self._render_labeled_bar(screen, "INTEGRITY", tick.integrity, YELLOW, sb_x + pad, curr_y, inner_w, row_h, ui)

    def _render_labeled_bar(self, screen, label, value, color, x, y, w, row_h, ui):
        lbl_txt = self.font_sm.render(label, True, (180, 195, 220))
        screen.blit(lbl_txt, (x, y))
        
        val_txt = self.font_sm.render(f"{value:.2f}", True, WHITE)
        screen.blit(val_txt, (x + w - val_txt.get_width(), y))
        
        bar_y = y + (ui.y(16) if ui else 16)
        bar_h = ui.h(6) if ui else 6
        self._render_bar(screen, x, bar_y, w, bar_h, value, color, ui)
        return y + row_h + (ui.y(12) if ui else 12)

    def _render_bar(self, screen, x, y, w, h, fill_ratio, color, ui):
        norm_ratio = max(0.0, min(float(fill_ratio), 1.0))
        pygame.draw.rect(screen, (30, 34, 50), (x, y, w, h), 0, ui.r(2) if ui else 2)
        if norm_ratio > 0:
            pygame.draw.rect(screen, color, (x, y, int(w * norm_ratio), h), 0, ui.r(2) if ui else 2)