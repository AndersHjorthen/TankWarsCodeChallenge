# -*- coding: utf-8 -*-

import pygame
import game_config as cfg


class Obstacle:
    """Rectangle obstacle that blocks tank movement and shot passage."""

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self._surface = self._build_surface()

    def _build_surface(self):
        """Pre-render a textured obstacle surface with hash pattern and edge shading."""
        surf = pygame.Surface((self.width, self.height))
        surf.fill(cfg.OBSTACLE_FILL_COLOR)

        # Diagonal hash pattern
        spacing = cfg.OBSTACLE_HASH_SPACING
        hc = cfg.OBSTACLE_HASH_COLOR
        for offset in range(-self.height, self.width + self.height, spacing):
            pygame.draw.line(surf, hc, (offset, 0), (offset + self.height, self.height))

        # Highlight edge (top and left)
        hl = cfg.OBSTACLE_HIGHLIGHT_COLOR
        pygame.draw.line(surf, hl, (0, 0), (self.width - 1, 0), 2)   # top
        pygame.draw.line(surf, hl, (0, 0), (0, self.height - 1), 2)   # left

        # Shadow edge (bottom and right)
        sh = cfg.OBSTACLE_SHADOW_COLOR
        pygame.draw.line(surf, sh, (0, self.height - 1), (self.width - 1, self.height - 1), 2)
        pygame.draw.line(surf, sh, (self.width - 1, 0), (self.width - 1, self.height - 1), 2)

        # Border
        bw = cfg.OBSTACLE_BORDER_WIDTH_NEW
        pygame.draw.rect(surf, cfg.OBSTACLE_BORDER_COLOR, (0, 0, self.width, self.height), bw)

        return surf

    def render(self, surface, color=None, border_color=None):
        """Draw the pre-rendered textured obstacle."""
        surface.blit(self._surface, (self.x, self.y))

    def collides_with_rect(self, other_rect):
        """Check if a pygame.Rect overlaps with this obstacle."""
        return self.rect.colliderect(other_rect)

    def contains_point(self, x, y, margin=0):
        """Check if a point (with optional margin) is inside this obstacle."""
        return (self.x - margin <= x <= self.x + self.width + margin and
                self.y - margin <= y <= self.y + self.height + margin)
