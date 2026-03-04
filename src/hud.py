# -*- coding: utf-8 -*-
"""HUD overlay: scoreboard, centered timer, and kill feed."""

import time
import pygame
import game_config as cfg

# Cached fonts (initialized lazily)
_hud_font = None
_timer_font = None


def _get_hud_font():
    global _hud_font
    if _hud_font is None:
        _hud_font = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_VSMALL)
    return _hud_font


def _get_timer_font():
    global _timer_font
    if _timer_font is None:
        _timer_font = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_SMALL, bold=True)
    return _timer_font


class KillFeed:
    """Displays recent kill events in the top-right corner."""

    def __init__(self):
        self.entries = []  # list of (time, killer_name, killer_color, victim_name, victim_color)

    def add_kill(self, killer_name, killer_color, victim_name, victim_color):
        self.entries.append((time.time(), killer_name, killer_color, victim_name, victim_color))

    def render(self, surface):
        now = time.time()
        # Remove expired entries
        self.entries = [e for e in self.entries
                        if now - e[0] < cfg.HUD_KILLFEED_DISPLAY_SECS]

        if not self.entries:
            return

        font = _get_hud_font()
        x_right = cfg.DISPLAY_WIDTH - cfg.HUD_KILLFEED_POS[0]
        y_start = cfg.HUD_KILLFEED_POS[1]

        # Draw background panel
        max_width = 250
        panel_h = len(self.entries) * cfg.HUD_KILLFEED_LINE_HEIGHT + 8
        panel_surf = pygame.Surface((max_width, panel_h), pygame.SRCALPHA)
        panel_surf.fill((*cfg.HUD_SCOREBOARD_BG_COLOR, cfg.HUD_KILLFEED_BG_ALPHA))
        surface.blit(panel_surf, (x_right - max_width, y_start))

        for i, (_, killer, k_color, victim, v_color) in enumerate(
                self.entries[-cfg.HUD_KILLFEED_MAX_ENTRIES:]):
            y = y_start + 4 + i * cfg.HUD_KILLFEED_LINE_HEIGHT

            k_surf = font.render(killer, True, k_color)
            arrow_surf = font.render(" > ", True, cfg.COLOR_GREY)
            v_surf = font.render(victim, True, v_color)

            total_w = k_surf.get_width() + arrow_surf.get_width() + v_surf.get_width()
            x = x_right - total_w - 8
            surface.blit(k_surf, (x, y))
            x += k_surf.get_width()
            surface.blit(arrow_surf, (x, y))
            x += arrow_surf.get_width()
            surface.blit(v_surf, (x, y))


class HUD:
    """Heads-up display with scoreboard, timer, and kill feed."""

    def __init__(self):
        self.kill_feed = KillFeed()

    def render(self, surface, tanks, time_remaining):
        """Render the full HUD overlay."""
        self._render_scoreboard(surface, tanks)
        self._render_timer(surface, time_remaining)
        self.kill_feed.render(surface)

    def _render_scoreboard(self, surface, tanks):
        """Top-left scoreboard panel showing player names, kills, damage."""
        if not tanks:
            return

        font = _get_hud_font()
        x, y = cfg.HUD_SCOREBOARD_POS
        line_h = cfg.HUD_SCOREBOARD_LINE_HEIGHT
        w = cfg.HUD_SCOREBOARD_WIDTH

        # Sort by kills then damage
        sorted_tanks = sorted(tanks, key=lambda t: (t.kills, t.damage_dealt), reverse=True)

        # Background panel
        panel_h = (len(sorted_tanks) + 1) * line_h + 8
        panel = pygame.Surface((w, panel_h), pygame.SRCALPHA)
        panel.fill((*cfg.HUD_SCOREBOARD_BG_COLOR, cfg.HUD_SCOREBOARD_BG_ALPHA))
        surface.blit(panel, (x, y))

        # Header
        header = font.render("Name        K   Dmg", True, cfg.COLOR_GREY)
        surface.blit(header, (x + 6, y + 4))

        for i, tank in enumerate(sorted_tanks):
            ty = y + 4 + (i + 1) * line_h
            color = getattr(tank, "team_color", cfg.COLOR_WHITE)
            line = f"{tank.name[:10]:<12}{tank.kills:<4}{int(tank.damage_dealt)}"
            text = font.render(line, True, color)
            surface.blit(text, (x + 6, ty))

    def _render_timer(self, surface, time_remaining):
        """Centered timer at the top with color coding."""
        font = _get_timer_font()

        minutes = int(time_remaining) // 60
        seconds = int(time_remaining) % 60
        timer_str = f"{minutes}:{seconds:02d}"

        # Color coding
        if time_remaining <= cfg.HUD_TIMER_CRITICAL_SECS:
            color = cfg.HUD_TIMER_COLOR_CRITICAL
        elif time_remaining <= cfg.HUD_TIMER_WARNING_SECS:
            color = cfg.HUD_TIMER_COLOR_WARNING
        else:
            color = cfg.HUD_TIMER_COLOR_NORMAL

        text = font.render(timer_str, True, color)
        rect = text.get_rect(midtop=(cfg.DISPLAY_WIDTH // 2, 8))

        # Shadow
        shadow = font.render(timer_str, True, (0, 0, 0))
        shadow_rect = shadow.get_rect(midtop=(rect.centerx + 1, rect.top + 1))
        surface.blit(shadow, shadow_rect)

        surface.blit(text, rect)
