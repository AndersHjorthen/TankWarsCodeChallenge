# -*- coding: utf-8 -*-
"""Pre-rendered arena background with grid and decorative borders."""

import pygame
import game_config as cfg


class ArenaRenderer:
    """Renders a pre-baked arena background surface (generated once at init)."""

    def __init__(self, width=None, height=None):
        self.width = width or cfg.DISPLAY_WIDTH
        self.height = height or cfg.DISPLAY_HEIGHT
        self.surface = self._build_surface()

    def _build_surface(self):
        surf = pygame.Surface((self.width, self.height))
        surf.fill(cfg.ARENA_BG_COLOR)

        # Subtle grid lines
        for x in range(0, self.width, cfg.ARENA_GRID_SPACING):
            pygame.draw.line(surf, cfg.ARENA_GRID_COLOR, (x, 0), (x, self.height))
        for y in range(0, self.height, cfg.ARENA_GRID_SPACING):
            pygame.draw.line(surf, cfg.ARENA_GRID_COLOR, (0, y), (self.width, y))

        # Double-line border
        bw = cfg.ARENA_BORDER_WIDTH
        gap = cfg.ARENA_BORDER_GAP

        # Outer border
        pygame.draw.rect(surf, cfg.ARENA_BORDER_COLOR_OUTER,
                         (0, 0, self.width, self.height), bw)
        # Inner border
        pygame.draw.rect(surf, cfg.ARENA_BORDER_COLOR_INNER,
                         (bw + gap, bw + gap,
                          self.width - 2 * (bw + gap),
                          self.height - 2 * (bw + gap)), bw)

        # Corner accents
        cl = cfg.ARENA_CORNER_ACCENT_LEN
        cc = cfg.ARENA_CORNER_ACCENT_COLOR
        inset = bw + gap + bw + 2
        corners = [
            # top-left
            ((inset, inset), (inset + cl, inset), (inset, inset + cl)),
            # top-right
            ((self.width - inset, inset), (self.width - inset - cl, inset),
             (self.width - inset, inset + cl)),
            # bottom-left
            ((inset, self.height - inset), (inset + cl, self.height - inset),
             (inset, self.height - inset - cl)),
            # bottom-right
            ((self.width - inset, self.height - inset),
             (self.width - inset - cl, self.height - inset),
             (self.width - inset, self.height - inset - cl)),
        ]
        for corner_pt, h_end, v_end in corners:
            pygame.draw.line(surf, cc, corner_pt, h_end, 2)
            pygame.draw.line(surf, cc, corner_pt, v_end, 2)

        return surf

    def render(self, target_surface):
        """Blit the pre-rendered background onto the target surface."""
        target_surface.blit(self.surface, (0, 0))
