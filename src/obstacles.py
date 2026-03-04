# -*- coding: utf-8 -*-

import pygame


class Obstacle:
    """Rectangle obstacle that blocks tank movement and shot passage."""

    def __init__(self, x, y, width, height):
        """
        Create an obstacle at the given position with the given dimensions.

        :param x: X coordinate of the top-left corner.
        :param y: Y coordinate of the top-left corner.
        :param width: Width of the obstacle in pixels.
        :param height: Height of the obstacle in pixels.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)

    def render(self, surface, color, border_color):
        """Draw the obstacle on the given surface."""
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)

    def collides_with_rect(self, other_rect):
        """Check if a pygame.Rect overlaps with this obstacle."""
        return self.rect.colliderect(other_rect)

    def contains_point(self, x, y, margin=0):
        """Check if a point (with optional margin) is inside this obstacle."""
        return (self.x - margin <= x <= self.x + self.width + margin and
                self.y - margin <= y <= self.y + self.height + margin)
