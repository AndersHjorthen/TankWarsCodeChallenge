# -*- coding: utf-8 -*-

import pygame
import random
import time


class PowerUp:
    """A collectible power-up that grants temporary effects to a tank."""

    TYPES = ["speed_boost", "rapid_fire", "shield"]

    def __init__(self, x, y, power_type):
        """
        Create a power-up at the given position.

        :param x: X coordinate of the power-up center.
        :param y: Y coordinate of the power-up center.
        :param power_type: One of "speed_boost", "rapid_fire", "shield".
        """
        if power_type not in self.TYPES:
            raise ValueError(f"Invalid power-up type: {power_type}. Must be one of {self.TYPES}")
        self.x = x
        self.y = y
        self.power_type = power_type
        self.spawn_time = time.time()
        self.alive = True

    def render(self, surface, colors, labels, radius):
        """
        Draw the power-up on the given surface.

        :param surface: Pygame surface to draw on.
        :param colors: Dict mapping power_type to RGB tuple.
        :param labels: Dict mapping power_type to single-character string.
        :param radius: Radius of the circle to draw.
        """
        if not self.alive:
            return

        color = colors.get(self.power_type, (255, 255, 255))
        center = (int(self.x), int(self.y))

        # Draw outer glow (pulsing)
        pulse = abs(((pygame.time.get_ticks() % 1000) / 1000.0) - 0.5) * 2.0
        glow_radius = int(radius + 4 * pulse)
        glow_color = tuple(min(255, c + 60) for c in color)
        pygame.draw.circle(surface, glow_color, center, glow_radius, 2)

        # Draw filled circle
        pygame.draw.circle(surface, color, center, radius)

        # Draw border
        pygame.draw.circle(surface, (255, 255, 255), center, radius, 2)

        # Draw label character
        label = labels.get(self.power_type, "?")
        font = pygame.font.SysFont("Arial", 16, bold=True)
        text_surface = font.render(label, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=center)
        surface.blit(text_surface, text_rect)

    def get_pickup_rect(self, pickup_radius):
        """Return a pygame.Rect for collision detection."""
        return pygame.Rect(
            self.x - pickup_radius,
            self.y - pickup_radius,
            pickup_radius * 2,
            pickup_radius * 2,
        )

    @staticmethod
    def spawn_random(display_width, display_height, obstacles, margin=60):
        """
        Spawn a power-up at a random valid position (not on obstacles, not too close to edges).

        :param display_width: Width of the arena.
        :param display_height: Height of the arena.
        :param obstacles: List of Obstacle objects to avoid.
        :param margin: Minimum distance from arena edges.
        :return: A new PowerUp instance, or None if no valid position found after attempts.
        """
        power_type = random.choice(PowerUp.TYPES)

        for _ in range(50):  # Try up to 50 times to find a valid position
            x = random.randint(margin, display_width - margin)
            y = random.randint(margin, display_height - margin)

            # Check that it does not overlap any obstacle
            on_obstacle = False
            for obs in obstacles:
                if obs.contains_point(x, y, margin=20):
                    on_obstacle = True
                    break

            if not on_obstacle:
                return PowerUp(x, y, power_type)

        # Fallback: place it anyway (very unlikely to reach here)
        return PowerUp(
            random.randint(margin, display_width - margin),
            random.randint(margin, display_height - margin),
            power_type,
        )


class ActiveEffect:
    """Tracks an active power-up effect on a player."""

    def __init__(self, power_type, duration):
        """
        :param power_type: The type of the power-up effect.
        :param duration: Duration in seconds.
        """
        self.power_type = power_type
        self.expiry_time = time.time() + duration

    def is_expired(self):
        return time.time() >= self.expiry_time

    def time_remaining(self):
        return max(0, self.expiry_time - time.time())
