# -*- coding: utf-8 -*-
"""Visual effects manager: smoke trails, tracers, muzzle flash, explosions,
hit flash, screen shake, and power-up aura."""

import math
import random
import time

import pygame

import game_config as cfg
from src.particles import ParticleSystem


class EffectsManager:
    """Central manager for all visual effects in the game."""

    def __init__(self):
        self.particles = ParticleSystem()
        self._screen_shake_end = 0.0
        self._screen_shake_intensity = 0
        self._hit_flash_tanks = {}  # tank -> flash_end_time

    # ------------------------------------------------------------------
    # Smoke trails (behind moving tanks)
    # ------------------------------------------------------------------
    def emit_smoke_trail(self, x, y):
        """Emit smoke particles at the given position (call each frame while tank moves)."""
        for _ in range(cfg.SMOKE_TRAIL_RATE):
            var = cfg.SMOKE_TRAIL_COLOR_VAR
            r, g, b = cfg.SMOKE_TRAIL_COLOR
            color = (r + random.randint(-var, var),
                     g + random.randint(-var, var),
                     b + random.randint(-var, var))
            color = tuple(max(0, min(255, c)) for c in color)
            vx = random.uniform(-cfg.SMOKE_TRAIL_SPEED, cfg.SMOKE_TRAIL_SPEED)
            vy = random.uniform(-cfg.SMOKE_TRAIL_SPEED, cfg.SMOKE_TRAIL_SPEED)
            self.particles.emit(x, y, vx, vy,
                                cfg.SMOKE_TRAIL_SIZE, color, cfg.SMOKE_TRAIL_LIFETIME)

    # ------------------------------------------------------------------
    # Shot tracers
    # ------------------------------------------------------------------
    def emit_tracer(self, x, y):
        """Emit tracer particles behind a shot (call each frame)."""
        for _ in range(cfg.TRACER_RATE):
            var = cfg.TRACER_COLOR_VAR
            r, g, b = cfg.TRACER_COLOR
            color = (r + random.randint(-var, var),
                     g + random.randint(-var, var),
                     b + random.randint(-var, var))
            color = tuple(max(0, min(255, c)) for c in color)
            vx = random.uniform(-cfg.TRACER_SPEED, cfg.TRACER_SPEED)
            vy = random.uniform(-cfg.TRACER_SPEED, cfg.TRACER_SPEED)
            self.particles.emit(x, y, vx, vy,
                                cfg.TRACER_SIZE, color, cfg.TRACER_LIFETIME)

    # ------------------------------------------------------------------
    # Muzzle flash
    # ------------------------------------------------------------------
    def emit_muzzle_flash(self, x, y, direction_angle_deg):
        """Emit a burst of bright particles at the muzzle."""
        self.particles.emit_burst(
            x, y,
            count=cfg.MUZZLE_FLASH_PARTICLES,
            speed=cfg.MUZZLE_FLASH_SPEED,
            size=cfg.MUZZLE_FLASH_SIZE,
            colors=[cfg.MUZZLE_FLASH_COLOR, (255, 255, 200)],
            lifetime=cfg.MUZZLE_FLASH_LIFETIME,
            spread=60,
            angle_offset=direction_angle_deg,
            size_var=2.0,
            speed_var=1.5,
        )

    # ------------------------------------------------------------------
    # Particle-based explosion
    # ------------------------------------------------------------------
    def emit_explosion(self, x, y, big=False):
        """Emit fire + debris particles at (x, y)."""
        count = cfg.EXPLOSION_PARTICLE_COUNT * (2 if big else 1)
        self.particles.emit_burst(
            x, y,
            count=count,
            speed=cfg.EXPLOSION_PARTICLE_SPEED * (1.3 if big else 1.0),
            size=cfg.EXPLOSION_PARTICLE_SIZE,
            colors=cfg.EXPLOSION_FIRE_COLORS,
            lifetime=cfg.EXPLOSION_PARTICLE_LIFETIME,
            spread=360,
            size_var=2.0,
            speed_var=2.0,
        )
        # Debris chunks
        debris_count = cfg.DEBRIS_PARTICLE_COUNT * (2 if big else 1)
        var = cfg.DEBRIS_COLOR_VAR
        debris_colors = []
        r, g, b = cfg.DEBRIS_COLOR
        for _ in range(4):
            debris_colors.append((
                max(0, min(255, r + random.randint(-var, var))),
                max(0, min(255, g + random.randint(-var, var))),
                max(0, min(255, b + random.randint(-var, var))),
            ))
        self.particles.emit_burst(
            x, y,
            count=debris_count,
            speed=cfg.DEBRIS_PARTICLE_SPEED,
            size=cfg.DEBRIS_PARTICLE_SIZE,
            colors=debris_colors,
            lifetime=cfg.DEBRIS_PARTICLE_LIFETIME,
            spread=360,
            size_var=1.5,
            speed_var=1.5,
            fade=False,
        )

    # ------------------------------------------------------------------
    # Hit flash (brief white overlay on damaged tank)
    # ------------------------------------------------------------------
    def trigger_hit_flash(self, tank):
        self._hit_flash_tanks[id(tank)] = time.time() + cfg.HIT_FLASH_DURATION

    def render_hit_flash(self, surface, tank):
        """Draw a white overlay on the tank if it was recently hit."""
        end_time = self._hit_flash_tanks.get(id(tank))
        if end_time and time.time() < end_time:
            rect = tank.get_intersection_geometry()
            flash_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, 80))
            surface.blit(flash_surf, rect.topleft)

    # ------------------------------------------------------------------
    # Screen shake
    # ------------------------------------------------------------------
    def trigger_screen_shake(self):
        self._screen_shake_end = time.time() + cfg.SCREEN_SHAKE_DURATION
        self._screen_shake_intensity = cfg.SCREEN_SHAKE_INTENSITY

    @property
    def is_shaking(self):
        return time.time() < self._screen_shake_end

    def get_shake_offset(self):
        if not self.is_shaking:
            return (0, 0)
        remaining = self._screen_shake_end - time.time()
        ratio = remaining / cfg.SCREEN_SHAKE_DURATION
        intensity = int(self._screen_shake_intensity * ratio)
        return (random.randint(-intensity, intensity),
                random.randint(-intensity, intensity))

    # ------------------------------------------------------------------
    # Shot glow
    # ------------------------------------------------------------------
    def render_shot_glow(self, surface, x, y):
        """Draw an additive glow circle behind a shot."""
        r = cfg.SHOT_GLOW_RADIUS
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        cr, cg, cb = cfg.SHOT_GLOW_COLOR
        pygame.draw.circle(glow, (cr, cg, cb, cfg.SHOT_GLOW_ALPHA), (r, r), r)
        surface.blit(glow, (int(x) - r, int(y) - r), special_flags=pygame.BLEND_ADD)

    # ------------------------------------------------------------------
    # Power-up aura ring around affected tanks
    # ------------------------------------------------------------------
    def render_powerup_aura(self, surface, tank):
        """Draw pulsing aura rings for each active effect on the tank."""
        if not hasattr(tank, "active_effects"):
            return
        t = time.time()
        for effect in tank.active_effects:
            if effect.is_expired():
                continue
            color = cfg.POWERUP_COLORS.get(effect.power_type, (255, 255, 255))
            pulse = 0.5 + 0.5 * math.sin(t * cfg.AURA_PULSE_SPEED * 2 * math.pi)
            radius = int(cfg.AURA_RING_RADIUS + 4 * pulse)
            alpha = int(cfg.AURA_RING_ALPHA * (0.5 + 0.5 * pulse))
            aura = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            r, g, b = color
            pygame.draw.circle(aura, (r, g, b, alpha), (radius, radius),
                               radius, cfg.AURA_RING_WIDTH)
            cx, cy = int(tank.position.x), int(tank.position.y)
            surface.blit(aura, (cx - radius, cy - radius))

    # ------------------------------------------------------------------
    # Update & render particles
    # ------------------------------------------------------------------
    def update(self, dt):
        """Update all particles. dt is seconds since last frame."""
        self.particles.update(dt)
        # Clean up expired hit flashes
        now = time.time()
        self._hit_flash_tanks = {k: v for k, v in self._hit_flash_tanks.items() if v > now}

    def render_particles(self, surface):
        """Render all active particles."""
        self.particles.render(surface)
