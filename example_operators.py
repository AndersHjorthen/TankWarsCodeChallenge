# -*- coding: utf-8 -*-
"""Example AI operators for TankWars Code Challenge.

This module provides three different AI strategies that demonstrate various
approaches to implementing a TankOperator. Each operator uses the Vec math
utilities from src/vec.py for calculations.

Strategies:
    ChaserOperator  -- Aggressive: charges at the nearest enemy and shoots.
    DodgerOperator  -- Defensive: dodges incoming shots, shoots opportunistically.
    SniperOperator  -- Patient: stays still, carefully aims turret, fires when aligned.

Usage:
    from example_operators import ChaserOperator, DodgerOperator, SniperOperator
"""

import math
from tank_operator import OperatorActions, TankOperator
from src.vec import Vec


# ---------------------------------------------------------------------------
# Helper functions shared by multiple operators
# ---------------------------------------------------------------------------

def _angle_between(vec_a, vec_b):
    """Return the signed angle in radians from vec_a to vec_b.

    Positive values mean vec_b is counter-clockwise from vec_a (in standard
    math coordinates where +y is up). In the pygame coordinate system where
    +y points down, positive values correspond to a clockwise visual rotation.

    Returns a value in the range (-pi, pi].
    """
    angle_a = math.atan2(vec_a.y, vec_a.x)
    angle_b = math.atan2(vec_b.y, vec_b.x)
    diff = angle_b - angle_a

    # Normalize to (-pi, pi]
    while diff > math.pi:
        diff -= 2 * math.pi
    while diff <= -math.pi:
        diff += 2 * math.pi
    return diff


def _find_nearest_enemy(my_position, other_tanks):
    """Return the TankObject that is closest to my_position, or None.

    Uses Vec.magnitude() for distance calculation.
    """
    nearest = None
    best_dist_sq = float("inf")
    for enemy in other_tanks:
        diff = enemy.position - my_position
        dist_sq = diff.x * diff.x + diff.y * diff.y  # avoid sqrt for comparison
        if dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            nearest = enemy
    return nearest


def _turn_signal(angle_diff, threshold=0.0):
    """Convert an angle difference into a turn value in [-1, 1].

    If the absolute angle difference is below *threshold* (radians), return 0.
    Otherwise return +1 (turn right / clockwise) or -1 (turn left / counter-clockwise).
    """
    if abs(angle_diff) <= threshold:
        return 0.0
    return 1.0 if angle_diff > 0 else -1.0


def _proportional_turn(angle_diff, max_turn_speed_rad=math.radians(7.5)):
    """Return a proportional turn value in [-1, 1] for the given angle difference.

    This gives smoother aiming than the simple bang-bang _turn_signal. The
    result is clamped to [-1, 1] by the game server, but we do it here too
    for clarity.
    """
    if max_turn_speed_rad == 0:
        return 0.0
    raw = angle_diff / max_turn_speed_rad
    return max(-1.0, min(1.0, raw))


# ===========================================================================
# ChaserOperator
# ===========================================================================

class ChaserOperator(TankOperator):
    """Aggressive AI that targets the nearest enemy, drives towards it, and fires.

    Strategy overview:
        1. Find the nearest enemy tank.
        2. Turn the tank body towards the enemy.
        3. Drive forward at full speed towards them.
        4. Turn the turret independently towards the enemy for quicker aiming.
        5. Fire when the turret is roughly aligned with the target.

    The chaser is effective at close range but can be outmaneuvered by agile
    opponents. It does not attempt to dodge incoming shots.

    Teaching points:
        - Demonstrates finding the nearest enemy with Vec subtraction and magnitude.
        - Shows how to independently aim the turret while driving the tank body.
        - Uses _angle_between to compute the signed angle to a target.
    """

    # The turret alignment threshold in radians. The chaser fires when the
    # turret is within this angle of the target direction.
    FIRE_THRESHOLD_RAD = math.radians(10)

    def get_operator_name(self):
        return "Chaser"

    def get_tank_action(self, game_state):
        actions = OperatorActions()
        my_tank = game_state.tank

        # Step 1: Find the nearest enemy
        target = _find_nearest_enemy(my_tank.position, game_state.other_tanks)
        if target is None:
            # No enemies visible -- just spin and look for targets
            actions.turn = 1.0
            return actions

        # Step 2: Compute the direction vector from our tank to the target
        to_target = target.position - my_tank.position

        # Step 3: Turn the tank body towards the target
        body_angle_diff = _angle_between(my_tank.direction, to_target)
        actions.turn = _proportional_turn(body_angle_diff)

        # Step 4: Drive forward. Slow down a bit if we are turning sharply
        # to avoid overshooting. Full speed when roughly aligned.
        if abs(body_angle_diff) < math.radians(30):
            actions.engine = 1.0
        elif abs(body_angle_diff) < math.radians(90):
            actions.engine = 0.5
        else:
            # We are facing away -- still move forward slowly while turning
            actions.engine = 0.2

        # Step 5: Turn the turret towards the target independently.
        # The turret rotates faster than the tank body (20 deg/frame vs 7.5),
        # so we use the turret turn speed for proportional control.
        turret_angle_diff = _angle_between(my_tank.turret_direction, to_target)
        actions.turn_turret = _proportional_turn(
            turret_angle_diff, max_turn_speed_rad=math.radians(20)
        )

        # Step 6: Fire when turret is aligned with the target
        if abs(turret_angle_diff) < self.FIRE_THRESHOLD_RAD:
            actions.shoot = True

        return actions


# ===========================================================================
# DodgerOperator
# ===========================================================================

class DodgerOperator(TankOperator):
    """Defensive AI that prioritizes dodging incoming shots.

    Strategy overview:
        1. Scan all active shots and determine which ones are heading towards us.
        2. If a threatening shot is detected, dodge by turning perpendicular to
           the shot's direction and driving away.
        3. When no immediate threat exists, opportunistically aim and fire at the
           nearest enemy.

    The dodger is hard to hit but less aggressive. It relies on survival and
    opportunistic shots rather than chasing enemies down.

    Teaching points:
        - Demonstrates how to assess incoming shot threats using dot product.
        - Shows how to compute a perpendicular dodge direction.
        - Balances defensive and offensive behavior based on threat assessment.
    """

    # Distance threshold: shots further away than this are not considered threats.
    THREAT_DISTANCE = 300.0

    # How close the shot needs to pass (perpendicular distance) to be a threat.
    THREAT_PROXIMITY = 80.0

    # Turret alignment threshold for opportunistic firing.
    FIRE_THRESHOLD_RAD = math.radians(8)

    def get_operator_name(self):
        return "Dodger"

    def _find_most_dangerous_shot(self, my_position, shots):
        """Find the incoming shot that is closest and heading towards us.

        Returns (shot, dodge_direction_vec) or (None, None) if no threat.

        A shot is considered a threat if:
            1. It is within THREAT_DISTANCE of our tank.
            2. It is moving towards us (dot product of shot direction and
               vector from shot to us is positive).
            3. The perpendicular miss distance is within THREAT_PROXIMITY.
        """
        best_shot = None
        best_dodge = None
        best_danger = float("inf")  # lower = more dangerous

        for shot in shots:
            # Vector from shot to our tank
            shot_to_me = my_position - shot.position
            dist = shot_to_me.magnitude()

            if dist > self.THREAT_DISTANCE or dist < 1.0:
                continue

            # Check if shot is heading towards us (positive dot product)
            shot_dir_norm = shot.direction.normalize()
            dot = shot_to_me.dot(shot_dir_norm)
            if dot <= 0:
                # Shot is moving away from us
                continue

            # Compute perpendicular distance from our position to the shot's line
            # Using: perp_dist = |shot_to_me - projection_on_shot_dir|
            projection = shot_dir_norm * dot
            perp_vec = shot_to_me - projection
            perp_dist = perp_vec.magnitude()

            if perp_dist > self.THREAT_PROXIMITY:
                # Shot will miss by a wide margin
                continue

            # This shot is a threat. Determine dodge direction:
            # Move perpendicular to the shot direction. Choose the side
            # that is already further from the shot line (so we move away).
            # Perpendicular directions: rotate shot_dir by +90 and -90 degrees
            perp_left = Vec(-shot_dir_norm.y, shot_dir_norm.x)
            perp_right = Vec(shot_dir_norm.y, -shot_dir_norm.x)

            # Pick the perpendicular direction that moves us further from the shot line
            if perp_vec.dot(perp_left) >= 0:
                dodge_dir = perp_left
            else:
                dodge_dir = perp_right

            # Use distance as danger metric (closer = more dangerous)
            if dist < best_danger:
                best_danger = dist
                best_shot = shot
                best_dodge = dodge_dir

        return best_shot, best_dodge

    def get_tank_action(self, game_state):
        actions = OperatorActions()
        my_tank = game_state.tank

        # Step 1: Check for incoming shot threats
        threat, dodge_dir = self._find_most_dangerous_shot(
            my_tank.position, game_state.shots
        )

        if threat is not None and dodge_dir is not None:
            # DODGE MODE: Turn towards dodge direction and drive at full speed
            body_angle_diff = _angle_between(my_tank.direction, dodge_dir)
            actions.turn = _proportional_turn(body_angle_diff)
            actions.engine = 1.0  # Full speed evasion

            # While dodging, still aim turret at nearest enemy opportunistically
            target = _find_nearest_enemy(my_tank.position, game_state.other_tanks)
            if target is not None:
                to_target = target.position - my_tank.position
                turret_angle_diff = _angle_between(my_tank.turret_direction, to_target)
                actions.turn_turret = _proportional_turn(
                    turret_angle_diff, max_turn_speed_rad=math.radians(20)
                )
                if abs(turret_angle_diff) < self.FIRE_THRESHOLD_RAD:
                    actions.shoot = True
        else:
            # PATROL MODE: No immediate threats -- aim at nearest enemy and shoot
            target = _find_nearest_enemy(my_tank.position, game_state.other_tanks)
            if target is not None:
                to_target = target.position - my_tank.position
                distance = to_target.magnitude()

                # Turn body towards enemy but move slowly (conserve position)
                body_angle_diff = _angle_between(my_tank.direction, to_target)
                actions.turn = _proportional_turn(body_angle_diff)

                # Move towards enemy at moderate speed
                if abs(body_angle_diff) < math.radians(45):
                    actions.engine = 0.4
                else:
                    actions.engine = 0.1

                # Aim turret at enemy
                turret_angle_diff = _angle_between(my_tank.turret_direction, to_target)
                actions.turn_turret = _proportional_turn(
                    turret_angle_diff, max_turn_speed_rad=math.radians(20)
                )

                # Fire when aligned
                if abs(turret_angle_diff) < self.FIRE_THRESHOLD_RAD:
                    actions.shoot = True
            else:
                # No enemies at all -- spin to search
                actions.turn = 1.0

        return actions


# ===========================================================================
# SniperOperator
# ===========================================================================

class SniperOperator(TankOperator):
    """Patient AI that stays relatively still and carefully aims before firing.

    Strategy overview:
        1. Keep the tank body mostly stationary (very slow or no movement).
        2. Slowly rotate the turret to track the nearest enemy.
        3. Only fire when the turret is very precisely aligned with the target.
        4. If health is low (when available), back away slowly from threats.

    The sniper conserves ammunition (due to the 5-second cooldown) by only
    firing well-aimed shots. It is vulnerable to rushing enemies but punishes
    opponents that hold still.

    Teaching points:
        - Demonstrates precise turret aiming with a tight fire threshold.
        - Shows how to use the enriched GameState (my_health, arena dimensions).
        - Illustrates a minimal-movement strategy focused on accuracy.
    """

    # Very tight turret alignment required before firing (about 3 degrees)
    FIRE_THRESHOLD_RAD = math.radians(3)

    # Health threshold below which the sniper tries to back away
    LOW_HEALTH_THRESHOLD = 80.0

    # Distance at which the sniper considers an enemy "too close" and backs away
    RETREAT_DISTANCE = 150.0

    def get_operator_name(self):
        return "Sniper"

    def get_tank_action(self, game_state):
        actions = OperatorActions()
        my_tank = game_state.tank

        # Find the nearest enemy to aim at
        target = _find_nearest_enemy(my_tank.position, game_state.other_tanks)
        if target is None:
            # No enemies visible -- slowly spin turret to scan
            actions.turn_turret = 0.5
            return actions

        # Vector from our tank to the target
        to_target = target.position - my_tank.position
        distance = to_target.magnitude()

        # --- Turret aiming (primary concern for the sniper) ---
        # Turn the turret precisely towards the target.
        turret_angle_diff = _angle_between(my_tank.turret_direction, to_target)
        actions.turn_turret = _proportional_turn(
            turret_angle_diff, max_turn_speed_rad=math.radians(20)
        )

        # Fire only when very precisely aligned
        if abs(turret_angle_diff) < self.FIRE_THRESHOLD_RAD:
            actions.shoot = True

        # --- Body movement (minimal, for positioning only) ---
        # The sniper stays mostly still. Turn the body slowly to face
        # the general direction of the enemy (helps with future shots
        # since the turret rotates with the body).
        body_angle_diff = _angle_between(my_tank.direction, to_target)
        actions.turn = _proportional_turn(body_angle_diff) * 0.3  # slow body turn

        # Check if we should retreat: if health is low or enemy is too close
        should_retreat = False

        # Use enriched GameState health info if available
        if game_state.my_health is not None:
            if game_state.my_health < self.LOW_HEALTH_THRESHOLD:
                should_retreat = True

        if distance < self.RETREAT_DISTANCE:
            should_retreat = True

        if should_retreat:
            # Back away from the enemy (reverse)
            if abs(body_angle_diff) < math.radians(90):
                # We are roughly facing the enemy -- reverse
                actions.engine = -0.5
            else:
                # We are facing away -- drive forward (away from enemy)
                actions.engine = 0.3
        else:
            # Stay mostly still. Only creep forward very slowly if aligned.
            if abs(body_angle_diff) < math.radians(20):
                actions.engine = 0.05
            else:
                actions.engine = 0.0

        # --- Arena boundary awareness ---
        # If arena dimensions are available, avoid getting stuck in corners
        if game_state.arena_width is not None and game_state.arena_height is not None:
            margin = 60.0
            pos = my_tank.position
            near_wall = (
                pos.x < margin
                or pos.x > game_state.arena_width - margin
                or pos.y < margin
                or pos.y > game_state.arena_height - margin
            )
            if near_wall:
                # Move towards center of arena
                center = Vec(game_state.arena_width / 2.0, game_state.arena_height / 2.0)
                to_center = center - pos
                center_angle_diff = _angle_between(my_tank.direction, to_center)
                actions.turn = _proportional_turn(center_angle_diff)
                actions.engine = 0.4

        return actions
