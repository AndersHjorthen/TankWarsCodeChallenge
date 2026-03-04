# -*- coding: utf-8 -*-
"""Reusable particle system for visual effects."""

import random
import pygame
import game_config as cfg


class Particle:
    """A single particle with position, velocity, size, color, and lifetime."""

    __slots__ = ("x", "y", "vx", "vy", "size", "color", "life", "max_life", "fade")

    def __init__(self, x, y, vx, vy, size, color, lifetime, fade=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.life = lifetime
        self.max_life = lifetime
        self.fade = fade


class ParticleSystem:
    """Manages a pool of particles with a hard cap for performance."""

    def __init__(self, max_particles=None):
        self.particles = []
        self.max_particles = max_particles or cfg.PARTICLE_MAX_COUNT

    def emit(self, x, y, vx, vy, size, color, lifetime, fade=True):
        """Add a single particle if under the cap."""
        if len(self.particles) >= self.max_particles:
            return
        self.particles.append(Particle(x, y, vx, vy, size, color, lifetime, fade))

    def emit_burst(self, x, y, count, speed, size, colors, lifetime,
                   spread=360, angle_offset=0, fade=True, size_var=0.0, speed_var=0.0):
        """Emit a burst of particles in a spread pattern."""
        import math
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            angle = math.radians(angle_offset + random.uniform(-spread / 2, spread / 2))
            s = speed + random.uniform(-speed_var, speed_var)
            vx = math.cos(angle) * s
            vy = math.sin(angle) * s
            sz = size + random.uniform(-size_var, size_var)
            color = random.choice(colors) if isinstance(colors, list) else colors
            self.particles.append(Particle(x, y, vx, vy, max(0.5, sz), color, lifetime, fade))

    def update(self, dt):
        """Update all particles and remove dead ones."""
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0 or p.size < cfg.PARTICLE_MIN_SIZE:
                continue
            p.x += p.vx
            p.y += p.vy
            # Shrink over lifetime
            ratio = p.life / p.max_life
            p.size *= (0.95 + 0.05 * ratio)
            alive.append(p)
        self.particles = alive

    def render(self, surface):
        """Draw all particles."""
        for p in self.particles:
            if p.fade:
                alpha = max(0, min(255, int(255 * (p.life / p.max_life))))
                s = max(1, int(p.size * 2))
                ps = pygame.Surface((s, s), pygame.SRCALPHA)
                r, g, b = p.color
                pygame.draw.circle(ps, (r, g, b, alpha), (s // 2, s // 2), max(1, int(p.size)))
                surface.blit(ps, (int(p.x) - s // 2, int(p.y) - s // 2))
            else:
                pygame.draw.circle(surface, p.color, (int(p.x), int(p.y)), max(1, int(p.size)))

    def clear(self):
        self.particles.clear()

    @property
    def count(self):
        return len(self.particles)
