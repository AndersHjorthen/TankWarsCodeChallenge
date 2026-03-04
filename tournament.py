#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Round-robin tournament runner for TankWars AI operators.

This module runs a round-robin tournament between multiple TankOperator classes,
tracking wins, losses, kills, and damage dealt across all matches. Results are
printed in a formatted table at the end.

NOTE: The current game server (tankwars_game_server.py) initializes pygame and
creates a display window at import time, which means this tournament runner
requires a display-capable environment. A fully headless mode would require
refactoring the game server to defer pygame initialization. For now, this runner
provides the tournament logic using a self-contained simulation engine that does
NOT depend on pygame, allowing it to run in headless environments (CI, SSH, etc.).

The simulation engine replicates the core game mechanics (movement, turning,
shooting, collision, damage) from the game server but without any rendering.

Usage:
    python tournament.py

    Or import and use programmatically:

        from tournament import run_tournament
        from example_operators import ChaserOperator, DodgerOperator, SniperOperator

        results = run_tournament([ChaserOperator, DodgerOperator, SniperOperator])
"""

import math
import time
import itertools
import sys
import os

# Ensure project root is on the path for imports
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.vec import Vec
from tank_operator import (
    TankOperator,
    TankObject,
    ShotObject,
    GameState,
    OperatorActions,
)
import game_config as cfg


# ---------------------------------------------------------------------------
# Headless simulation engine
# ---------------------------------------------------------------------------
# This engine replicates the core game logic from tankwars_game_server.py
# without any pygame dependency. It uses the same physics constants so
# tournament results closely mirror what would happen in the real game.
# ---------------------------------------------------------------------------

def _cap_value_zero_max(value, max_val):
    """Clamp a value to [0, max_val]. Returns (was_capped, clamped_value)."""
    if value > max_val or value < 0:
        return True, max(0.0, min(max_val, value))
    return False, value


def _turn_vector(vector, turn_action_scalar, max_turn_speed):
    """Rotate a direction vector in place, matching GameEntity.turn_vector."""
    current_angle = math.atan2(vector.y, vector.x)
    turn_value = max(-1.0, min(1.0, turn_action_scalar))
    angle_change = turn_value * max_turn_speed
    new_angle = current_angle + angle_change
    vector.x = math.cos(new_angle)
    vector.y = math.sin(new_angle)
    norm = vector.normalize()
    vector.x = norm.x
    vector.y = norm.y


def _calculate_damage(shot_pos, shot_dir, tank_pos):
    """Pure reimplementation of calculate_damage from the game server."""
    line_direction = shot_dir.normalize()
    point_vector = (tank_pos - shot_pos).normalize()
    projection = point_vector.dot(line_direction)
    closest_point_on_line = shot_pos + line_direction * projection
    distance_vector = tank_pos - closest_point_on_line
    dmg = cfg.MAX_SHOT_DAMAGE * distance_vector.magnitude() / cfg.DAMAGE_DIVISOR
    return dmg


class _SimTank:
    """Simulated tank for headless match execution."""

    def __init__(self, operator, position, direction):
        self.operator = operator
        self.name = operator.get_operator_name()
        self.position = Vec(position.x, position.y)
        self.direction = Vec(direction.x, direction.y)
        # Normalize direction
        norm = self.direction.normalize()
        self.direction.x = norm.x
        self.direction.y = norm.y
        self.turret_direction = Vec(self.direction)
        self.health = cfg.TANK_START_HEALTH
        self.kills = 0
        self.damage_dealt = 0.0
        self.last_shot_time = -999.0  # allow immediate first shot

    def get_gamestate_object(self):
        return TankObject(
            Vec(self.position), Vec(self.direction), Vec(self.turret_direction)
        )

    def apply_turn(self, operator_actions):
        _turn_vector(self.direction, operator_actions.turn, cfg.TANK_TURN_SPEED)
        _turn_vector(self.turret_direction, operator_actions.turn, cfg.TANK_TURN_SPEED)
        _turn_vector(
            self.turret_direction, operator_actions.turn_turret, cfg.TANK_TURRET_TURN_SPEED
        )

    def move(self, engine_scalar, arena_w, arena_h):
        speed_val = max(-1.0, min(1.0, engine_scalar))
        move_vec = self.direction * speed_val * cfg.TANK_MAX_SPEED
        self.position = self.position + move_vec
        _, self.position.x = _cap_value_zero_max(self.position.x, arena_w)
        _, self.position.y = _cap_value_zero_max(self.position.y, arena_h)


class _SimShot:
    """Simulated shot for headless match execution."""

    def __init__(self, owner_tank):
        self.position = Vec(owner_tank.position)
        self.direction = Vec(owner_tank.turret_direction)
        self.owner = owner_tank

    def get_gamestate_object(self):
        return ShotObject(Vec(self.position), Vec(self.direction))

    def move(self, arena_w, arena_h):
        """Move the shot. Returns True if it hit the arena boundary."""
        move_vec = self.direction * cfg.SHOT_SPEED
        self.position = self.position + move_vec
        cx, self.position.x = _cap_value_zero_max(self.position.x, arena_w)
        cy, self.position.y = _cap_value_zero_max(self.position.y, arena_h)
        return cx or cy


def _rects_collide(pos_a, size_a, pos_b, size_b):
    """Simple axis-aligned bounding box collision check.

    Each rect is defined by center position and (width, height).
    Uses the max dimension as a square, matching the game server's
    get_intersection_geometry() which uses max(width, height) as a square.
    """
    half_a = max(size_a) / 2.0
    half_b = max(size_b) / 2.0
    return (
        abs(pos_a.x - pos_b.x) < (half_a + half_b)
        and abs(pos_a.y - pos_b.y) < (half_a + half_b)
    )


def run_match(operator_a_class, operator_b_class, max_frames=None, quiet=True):
    """Run a single match between two operator classes. Returns match result dict.

    Args:
        operator_a_class: First TankOperator class (will be instantiated).
        operator_b_class: Second TankOperator class (will be instantiated).
        max_frames: Maximum number of simulation frames. Defaults to
            GAME_TIMEOUT_SECS * GAME_FPS (matching real game duration).
        quiet: If True, suppress per-frame output.

    Returns:
        dict with keys:
            'winner': name of winner (str) or 'Draw' if tie
            'tank_a': dict with name, kills, damage_dealt, health_remaining
            'tank_b': dict with name, kills, damage_dealt, health_remaining
    """
    arena_w = cfg.DISPLAY_WIDTH
    arena_h = cfg.DISPLAY_HEIGHT

    if max_frames is None:
        max_frames = cfg.GAME_TIMEOUT_SECS * cfg.GAME_FPS

    # Use the first two starting positions from the config
    pos_names = cfg.STARTING_POSITION_NAMES
    sp = cfg.STARTING_POSITIONS

    pos_a = Vec(sp[pos_names[0]]["pos"][0], sp[pos_names[0]]["pos"][1])
    dir_a = Vec(sp[pos_names[0]]["dir"][0], sp[pos_names[0]]["dir"][1])

    pos_b = Vec(sp[pos_names[1]]["pos"][0], sp[pos_names[1]]["pos"][1])
    dir_b = Vec(sp[pos_names[1]]["dir"][0], sp[pos_names[1]]["dir"][1])

    tank_a = _SimTank(operator_a_class(), pos_a, dir_a)
    tank_b = _SimTank(operator_b_class(), pos_b, dir_b)

    tanks = [tank_a, tank_b]
    shots = []
    sim_time = 0.0
    dt = 1.0 / cfg.GAME_FPS  # simulated time step per frame
    game_duration = cfg.GAME_TIMEOUT_SECS

    # Tank image sizes for collision detection
    tank_size = cfg.TANK_IMAGE_SIZE
    shot_size = cfg.SHOT_IMAGE_SIZE

    winner = None

    for frame in range(max_frames):
        sim_time = frame * dt
        time_remaining = max(0.0, game_duration - sim_time)

        # --- Update each tank ---
        for tank in list(tanks):
            other_tanks_gs = [t.get_gamestate_object() for t in tanks if t is not tank]
            shots_gs = [s.get_gamestate_object() for s in shots]

            gamestate = GameState(
                tank.get_gamestate_object(),
                other_tanks_gs,
                shots_gs,
                my_health=tank.health,
                arena_width=arena_w,
                arena_height=arena_h,
                game_time_remaining=time_remaining,
            )

            try:
                tank_actions = tank.operator.get_tank_action(gamestate)
            except Exception:
                tank_actions = OperatorActions()

            if tank_actions:
                # Check for shot
                if tank_actions.shoot:
                    if sim_time - tank.last_shot_time >= cfg.SHOT_COOLDOWN_SECS:
                        shots.append(_SimShot(tank))
                        tank.last_shot_time = sim_time

                tank.apply_turn(tank_actions)
                tank.move(tank_actions.engine, arena_w, arena_h)

        # --- Move shots and remove those hitting boundaries ---
        shots_to_remove = []
        for shot in shots:
            if shot.move(arena_w, arena_h):
                shots_to_remove.append(shot)
        for s in shots_to_remove:
            shots.remove(s)

        # --- Check for shot-tank collisions ---
        shots_hit = []
        tanks_killed = []
        for shot in shots:
            for tank in tanks:
                if tank is shot.owner:
                    continue
                if _rects_collide(shot.position, shot_size, tank.position, tank_size):
                    damage = _calculate_damage(shot.position, shot.direction, tank.position)
                    shot.owner.damage_dealt += damage
                    tank.health -= damage
                    shots_hit.append(shot)

                    if tank.health < 0:
                        shot.owner.kills += 1
                        tanks_killed.append(tank)
                    break  # shot can only hit one tank

        for s in shots_hit:
            if s in shots:
                shots.remove(s)
        for t in tanks_killed:
            if t in tanks:
                tanks.remove(t)

        # --- Check win conditions ---
        if len(tanks) == 1:
            winner = tanks[0].name
            break
        if len(tanks) == 0:
            winner = "Draw"
            break

        # --- Time out ---
        if time_remaining <= 0:
            # Winner is whoever dealt more damage
            if tank_a in tanks and tank_b in tanks:
                if tank_a.damage_dealt > tank_b.damage_dealt:
                    winner = tank_a.name
                elif tank_b.damage_dealt > tank_a.damage_dealt:
                    winner = tank_b.name
                else:
                    winner = "Draw"
            elif tank_a in tanks:
                winner = tank_a.name
            elif tank_b in tanks:
                winner = tank_b.name
            else:
                winner = "Draw"
            break

    # If we ran out of frames without a winner
    if winner is None:
        if tank_a.damage_dealt > tank_b.damage_dealt:
            winner = tank_a.name
        elif tank_b.damage_dealt > tank_a.damage_dealt:
            winner = tank_b.name
        else:
            winner = "Draw"

    return {
        "winner": winner,
        "tank_a": {
            "name": tank_a.name,
            "kills": tank_a.kills,
            "damage_dealt": round(tank_a.damage_dealt, 1),
            "health_remaining": round(max(0.0, tank_a.health), 1),
        },
        "tank_b": {
            "name": tank_b.name,
            "kills": tank_b.kills,
            "damage_dealt": round(tank_b.damage_dealt, 1),
            "health_remaining": round(max(0.0, tank_b.health), 1),
        },
    }


# ---------------------------------------------------------------------------
# Tournament runner
# ---------------------------------------------------------------------------

def run_tournament(operator_classes, matches_per_pair=3, max_frames_per_match=None, quiet=False):
    """Run a round-robin tournament between the given operator classes.

    Each pair plays *matches_per_pair* matches (to reduce randomness effects).
    For each pair, both operators play from both starting positions across the
    matches to ensure fairness.

    Args:
        operator_classes: List of TankOperator subclasses to compete.
        matches_per_pair: Number of matches each pair plays (default 3).
        max_frames_per_match: Override max frames per match (default: full game).
        quiet: If True, suppress per-match output.

    Returns:
        dict mapping operator name -> stats dict with:
            wins, losses, draws, kills, damage_dealt
    """
    if len(operator_classes) < 2:
        print("ERROR: Need at least 2 operator classes for a tournament.")
        return {}

    # Get operator names for display
    name_map = {}
    for cls in operator_classes:
        instance = cls()
        name_map[cls] = instance.get_operator_name()

    # Initialize stats
    stats = {}
    for cls in operator_classes:
        stats[name_map[cls]] = {
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "kills": 0,
            "damage_dealt": 0.0,
            "class": cls,
        }

    # Generate all pairings
    pairs = list(itertools.combinations(operator_classes, 2))
    total_matches = len(pairs) * matches_per_pair

    if not quiet:
        print("=" * 70)
        print("TANKWARS TOURNAMENT")
        print("=" * 70)
        print(f"Participants: {', '.join(name_map[c] for c in operator_classes)}")
        print(f"Matches per pair: {matches_per_pair}")
        print(f"Total matches: {total_matches}")
        print("-" * 70)

    match_num = 0
    for cls_a, cls_b in pairs:
        name_a = name_map[cls_a]
        name_b = name_map[cls_b]

        for i in range(matches_per_pair):
            match_num += 1
            # Alternate starting positions for fairness
            if i % 2 == 0:
                result = run_match(cls_a, cls_b, max_frames=max_frames_per_match)
                a_stats = result["tank_a"]
                b_stats = result["tank_b"]
            else:
                result = run_match(cls_b, cls_a, max_frames=max_frames_per_match)
                a_stats = result["tank_b"]
                b_stats = result["tank_a"]

            # Accumulate stats
            stats[name_a]["kills"] += a_stats["kills"]
            stats[name_a]["damage_dealt"] += a_stats["damage_dealt"]
            stats[name_b]["kills"] += b_stats["kills"]
            stats[name_b]["damage_dealt"] += b_stats["damage_dealt"]

            if result["winner"] == name_a:
                stats[name_a]["wins"] += 1
                stats[name_b]["losses"] += 1
                outcome_str = f"{name_a} wins"
            elif result["winner"] == name_b:
                stats[name_b]["wins"] += 1
                stats[name_a]["losses"] += 1
                outcome_str = f"{name_b} wins"
            else:
                stats[name_a]["draws"] += 1
                stats[name_b]["draws"] += 1
                outcome_str = "Draw"

            if not quiet:
                print(
                    f"  Match {match_num:>3}/{total_matches}: "
                    f"{name_a} vs {name_b} -> {outcome_str} "
                    f"(dmg: {a_stats['damage_dealt']:.0f} / {b_stats['damage_dealt']:.0f})"
                )

    # Remove class references from stats before returning
    clean_stats = {}
    for name, s in stats.items():
        clean_stats[name] = {k: v for k, v in s.items() if k != "class"}

    if not quiet:
        _print_results_table(clean_stats)

    return clean_stats


def _print_results_table(stats):
    """Print a formatted results table."""
    print()
    print("=" * 70)
    print("TOURNAMENT RESULTS")
    print("=" * 70)

    # Sort by wins descending, then by damage dealt descending
    sorted_names = sorted(
        stats.keys(),
        key=lambda n: (stats[n]["wins"], stats[n]["damage_dealt"]),
        reverse=True,
    )

    # Header
    header = (
        f"{'Rank':<6}{'Name':<15}{'W':>4}{'L':>4}{'D':>4}"
        f"{'Kills':>7}{'Damage':>10}{'Points':>8}"
    )
    print(header)
    print("-" * 70)

    for rank, name in enumerate(sorted_names, 1):
        s = stats[name]
        # Points: 3 for win, 1 for draw, 0 for loss
        points = s["wins"] * 3 + s["draws"] * 1
        row = (
            f"{rank:<6}{name:<15}{s['wins']:>4}{s['losses']:>4}{s['draws']:>4}"
            f"{s['kills']:>7}{s['damage_dealt']:>10.1f}{points:>8}"
        )
        print(row)

    print("=" * 70)
    print()

    # Announce winner
    winner_name = sorted_names[0]
    winner_stats = stats[winner_name]
    runner_up = sorted_names[1] if len(sorted_names) > 1 else None

    # Check for tie at the top
    if runner_up and (
        winner_stats["wins"] == stats[runner_up]["wins"]
        and winner_stats["damage_dealt"] == stats[runner_up]["damage_dealt"]
    ):
        print(f"TIED at the top: {winner_name} and {runner_up}!")
    else:
        print(f"CHAMPION: {winner_name} ({winner_stats['wins']} wins)")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from example_operators import ChaserOperator, DodgerOperator, SniperOperator
    from dummy_operator import DummyOperator

    print("Running TankWars Tournament (headless simulation)...")
    print()

    results = run_tournament(
        [ChaserOperator, DodgerOperator, SniperOperator, DummyOperator],
        matches_per_pair=3,
    )
