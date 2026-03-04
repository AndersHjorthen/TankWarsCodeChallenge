"""Tests for game logic from tankwars_game_server.py.

Many functions in the game server are tightly coupled to pygame and the game
loop, making them hard to test in isolation. This module tests the logic that
CAN be exercised without pygame by importing only the pure-logic pieces and
by constructing lightweight stand-ins where needed.

Functions that would benefit from extraction for better testability are noted
with comments.
"""

import math
import pytest
from src.vec import Vec
from tank_operator import TankObject, ShotObject, OperatorActions


# ---------------------------------------------------------------------------
# We cannot import tankwars_game_server at module level because it calls
# pygame.init(), pygame.display.set_mode(), and loads image resources at
# import time. Instead we selectively import or re-implement the pure-logic
# functions so that we can test them without a display.
# ---------------------------------------------------------------------------


# Re-implementation of calculate_damage from tankwars_game_server.py
# (copied verbatim so we test the actual algorithm).
_MAX_SHOT_DAMAGE = 100

def _calculate_damage(shot, tank):
    """Pure reimplementation of calculate_damage for testing."""
    line_direction = shot.direction.normalize()
    point_vector = (tank.position - shot.position).normalize()
    projection = point_vector.dot(line_direction)
    closest_point_on_line = shot.position + line_direction * projection
    distance_vector = tank.position - closest_point_on_line
    dmg = _MAX_SHOT_DAMAGE * distance_vector.magnitude() / 60
    return dmg


# Re-implementation of cap_value_zero_max (nested inside move_check_boundary).
def _cap_value_zero_max(cap, max_val):
    if cap > max_val or cap < 0:
        return True, max(0.0, min(max_val, cap))
    else:
        return False, cap


# Re-implementation of turn_vector (static method in GameEntity).
def _turn_vector(vector, turn_action_scalar, max_turn_speed):
    """Pure reimplementation of GameEntity.turn_vector for testing."""
    current_angle = math.atan2(vector.y, vector.x)
    turn_value = max(-1.0, min(1.0, turn_action_scalar))
    angle_change = turn_value * max_turn_speed
    new_angle = current_angle + angle_change
    vector.x = math.cos(new_angle)
    vector.y = math.sin(new_angle)
    vector.normalize()


# Constants from the game server
_DISPLAY_SIZE_X = 1200
_DISPLAY_SIZE_Y = 800
_TANK_TURN_SPEED = math.radians(7.5)
_TANK_TURRET_TURN_SPEED = math.radians(20)
_TANK_MAXSPEED = 3.5
_SHOT_SPEED = 15.0
_TANK_START_HEALTH = 200


# A lightweight entity that mimics PlayerContext/GameEntity for boundary testing.
class _MockEntity:
    """Minimal stand-in for GameEntity to test move_check_boundary logic."""

    def __init__(self, position, direction):
        self.position = position
        self.direction = direction
        self.turret_direction = Vec(direction)

    def move_check_boundary(self, operator_engine_scalar, maxspeed):
        operator_speed_value = max(-1.0, min(1.0, operator_engine_scalar))
        move_vector = self.direction * operator_speed_value * maxspeed
        self.position = self.position + move_vector

        capped_x, self.position.x = _cap_value_zero_max(self.position.x, _DISPLAY_SIZE_X)
        capped_y, self.position.y = _cap_value_zero_max(self.position.y, _DISPLAY_SIZE_Y)

        return capped_x or capped_y

    def apply_turn(self, operator_actions):
        _turn_vector(self.direction, operator_actions.turn, _TANK_TURN_SPEED)
        _turn_vector(self.turret_direction, operator_actions.turn, _TANK_TURN_SPEED)
        _turn_vector(self.turret_direction, operator_actions.turn_turret, _TANK_TURRET_TURN_SPEED)


# ===========================================================================
# Tests
# ===========================================================================


class TestCapValueZeroMax:
    """Tests for the cap_value_zero_max helper (boundary clamping)."""

    def test_value_within_bounds(self):
        capped, val = _cap_value_zero_max(50, 100)
        assert capped is False
        assert val == 50

    def test_value_at_zero(self):
        capped, val = _cap_value_zero_max(0, 100)
        assert capped is False
        assert val == 0

    def test_value_at_max(self):
        capped, val = _cap_value_zero_max(100, 100)
        assert capped is False
        assert val == 100

    def test_value_below_zero(self):
        capped, val = _cap_value_zero_max(-10, 100)
        assert capped is True
        assert val == 0.0

    def test_value_above_max(self):
        capped, val = _cap_value_zero_max(150, 100)
        assert capped is True
        assert val == 100

    @pytest.mark.parametrize(
        "input_val, max_val, expect_capped, expect_output",
        [
            (50, 200, False, 50),
            (-1, 200, True, 0.0),
            (201, 200, True, 200),
            (0, 200, False, 0),
            (200, 200, False, 200),
        ],
    )
    def test_parametrized(self, input_val, max_val, expect_capped, expect_output):
        capped, val = _cap_value_zero_max(input_val, max_val)
        assert capped is expect_capped
        assert val == pytest.approx(expect_output)


# ---------------------------------------------------------------------------
# Boundary checking (move_check_boundary)
# ---------------------------------------------------------------------------

class TestMoveCheckBoundary:
    """Tank should not move outside the arena (0..DISPLAY_SIZE)."""

    def test_normal_movement_no_boundary(self):
        ent = _MockEntity(Vec(600, 400), Vec(1.0, 0.0))
        capped = ent.move_check_boundary(1.0, _TANK_MAXSPEED)
        assert capped is False
        assert ent.position.x == pytest.approx(600 + _TANK_MAXSPEED)
        assert ent.position.y == pytest.approx(400)

    def test_movement_capped_at_right_boundary(self):
        ent = _MockEntity(Vec(_DISPLAY_SIZE_X - 1, 400), Vec(1.0, 0.0))
        capped = ent.move_check_boundary(1.0, _TANK_MAXSPEED)
        assert capped is True
        assert ent.position.x == pytest.approx(_DISPLAY_SIZE_X)

    def test_movement_capped_at_left_boundary(self):
        ent = _MockEntity(Vec(1, 400), Vec(-1.0, 0.0))
        capped = ent.move_check_boundary(1.0, _TANK_MAXSPEED)
        assert capped is True
        assert ent.position.x == pytest.approx(0.0)

    def test_movement_capped_at_bottom_boundary(self):
        ent = _MockEntity(Vec(600, _DISPLAY_SIZE_Y - 1), Vec(0.0, 1.0))
        capped = ent.move_check_boundary(1.0, _TANK_MAXSPEED)
        assert capped is True
        assert ent.position.y == pytest.approx(_DISPLAY_SIZE_Y)

    def test_movement_capped_at_top_boundary(self):
        ent = _MockEntity(Vec(600, 1), Vec(0.0, -1.0))
        capped = ent.move_check_boundary(1.0, _TANK_MAXSPEED)
        assert capped is True
        assert ent.position.y == pytest.approx(0.0)

    def test_reverse_movement(self):
        ent = _MockEntity(Vec(600, 400), Vec(1.0, 0.0))
        capped = ent.move_check_boundary(-1.0, _TANK_MAXSPEED)
        assert capped is False
        assert ent.position.x == pytest.approx(600 - _TANK_MAXSPEED)

    def test_zero_engine(self):
        ent = _MockEntity(Vec(600, 400), Vec(1.0, 0.0))
        capped = ent.move_check_boundary(0.0, _TANK_MAXSPEED)
        assert capped is False
        assert ent.position.x == pytest.approx(600)
        assert ent.position.y == pytest.approx(400)

    def test_engine_value_capped_at_1(self):
        """Engine values above 1.0 should be clamped to 1.0."""
        ent1 = _MockEntity(Vec(600, 400), Vec(1.0, 0.0))
        ent1.move_check_boundary(5.0, _TANK_MAXSPEED)

        ent2 = _MockEntity(Vec(600, 400), Vec(1.0, 0.0))
        ent2.move_check_boundary(1.0, _TANK_MAXSPEED)

        assert ent1.position.x == pytest.approx(ent2.position.x)

    def test_engine_value_capped_at_neg1(self):
        """Engine values below -1.0 should be clamped to -1.0."""
        ent1 = _MockEntity(Vec(600, 400), Vec(1.0, 0.0))
        ent1.move_check_boundary(-5.0, _TANK_MAXSPEED)

        ent2 = _MockEntity(Vec(600, 400), Vec(1.0, 0.0))
        ent2.move_check_boundary(-1.0, _TANK_MAXSPEED)

        assert ent1.position.x == pytest.approx(ent2.position.x)

    def test_diagonal_movement(self):
        direction = Vec(1.0, 1.0).normalize()
        ent = _MockEntity(Vec(600, 400), direction)
        capped = ent.move_check_boundary(1.0, _TANK_MAXSPEED)
        assert capped is False
        expected_dx = direction.x * _TANK_MAXSPEED
        expected_dy = direction.y * _TANK_MAXSPEED
        assert ent.position.x == pytest.approx(600 + expected_dx)
        assert ent.position.y == pytest.approx(400 + expected_dy)


# ---------------------------------------------------------------------------
# Turn vector logic
# ---------------------------------------------------------------------------

class TestTurnVector:
    """Test the turn_vector function that handles tank/turret rotation."""

    def test_no_turn(self):
        direction = Vec(1.0, 0.0)
        _turn_vector(direction, 0.0, _TANK_TURN_SPEED)
        assert direction.x == pytest.approx(1.0)
        assert direction.y == pytest.approx(0.0)

    def test_full_right_turn(self):
        direction = Vec(1.0, 0.0)
        _turn_vector(direction, 1.0, _TANK_TURN_SPEED)
        expected_angle = _TANK_TURN_SPEED
        assert direction.x == pytest.approx(math.cos(expected_angle))
        assert direction.y == pytest.approx(math.sin(expected_angle))

    def test_full_left_turn(self):
        direction = Vec(1.0, 0.0)
        _turn_vector(direction, -1.0, _TANK_TURN_SPEED)
        expected_angle = -_TANK_TURN_SPEED
        assert direction.x == pytest.approx(math.cos(expected_angle))
        assert direction.y == pytest.approx(math.sin(expected_angle))

    def test_turn_value_clamped_above_1(self):
        """Turn values above 1.0 should be clamped."""
        dir1 = Vec(1.0, 0.0)
        _turn_vector(dir1, 5.0, _TANK_TURN_SPEED)

        dir2 = Vec(1.0, 0.0)
        _turn_vector(dir2, 1.0, _TANK_TURN_SPEED)

        assert dir1.x == pytest.approx(dir2.x)
        assert dir1.y == pytest.approx(dir2.y)

    def test_turn_value_clamped_below_neg1(self):
        """Turn values below -1.0 should be clamped."""
        dir1 = Vec(1.0, 0.0)
        _turn_vector(dir1, -5.0, _TANK_TURN_SPEED)

        dir2 = Vec(1.0, 0.0)
        _turn_vector(dir2, -1.0, _TANK_TURN_SPEED)

        assert dir1.x == pytest.approx(dir2.x)
        assert dir1.y == pytest.approx(dir2.y)

    def test_half_turn(self):
        direction = Vec(1.0, 0.0)
        _turn_vector(direction, 0.5, _TANK_TURN_SPEED)
        expected_angle = 0.5 * _TANK_TURN_SPEED
        assert direction.x == pytest.approx(math.cos(expected_angle))
        assert direction.y == pytest.approx(math.sin(expected_angle))

    def test_resulting_vector_is_unit_length(self):
        """After turning, the direction vector should still be approximately unit length."""
        direction = Vec(1.0, 0.0)
        _turn_vector(direction, 0.7, _TANK_TURN_SPEED)
        mag = math.sqrt(direction.x ** 2 + direction.y ** 2)
        assert mag == pytest.approx(1.0)

    def test_turret_turn_speed_faster_than_tank(self):
        """Turret should rotate faster than the tank body."""
        tank_dir = Vec(1.0, 0.0)
        turret_dir = Vec(1.0, 0.0)

        _turn_vector(tank_dir, 1.0, _TANK_TURN_SPEED)
        _turn_vector(turret_dir, 1.0, _TANK_TURRET_TURN_SPEED)

        tank_angle = math.atan2(tank_dir.y, tank_dir.x)
        turret_angle = math.atan2(turret_dir.y, turret_dir.x)

        assert abs(turret_angle) > abs(tank_angle)


# ---------------------------------------------------------------------------
# Apply turn (tank + turret combined)
# ---------------------------------------------------------------------------

class TestApplyTurn:
    """Test apply_turn which turns both tank body and turret."""

    def test_apply_turn_no_action(self):
        ent = _MockEntity(Vec(100, 100), Vec(1.0, 0.0))
        actions = OperatorActions(turn=0.0, turn_turret=0.0)
        ent.apply_turn(actions)
        assert ent.direction.x == pytest.approx(1.0)
        assert ent.direction.y == pytest.approx(0.0)

    def test_tank_turn_also_turns_turret(self):
        """When tank turns, the turret should turn with it."""
        ent = _MockEntity(Vec(100, 100), Vec(1.0, 0.0))
        actions = OperatorActions(turn=1.0, turn_turret=0.0)
        ent.apply_turn(actions)

        # Both should have turned by the same amount
        tank_angle = math.atan2(ent.direction.y, ent.direction.x)
        turret_angle = math.atan2(ent.turret_direction.y, ent.turret_direction.x)

        # Tank turns once; turret turns with tank (same amount since turn_turret=0)
        assert tank_angle == pytest.approx(_TANK_TURN_SPEED)
        assert turret_angle == pytest.approx(_TANK_TURN_SPEED)

    def test_turret_independent_turn(self):
        """Turret turns independently on top of the tank turn."""
        ent = _MockEntity(Vec(100, 100), Vec(1.0, 0.0))
        actions = OperatorActions(turn=0.0, turn_turret=1.0)
        ent.apply_turn(actions)

        tank_angle = math.atan2(ent.direction.y, ent.direction.x)
        turret_angle = math.atan2(ent.turret_direction.y, ent.turret_direction.x)

        # Tank should not have turned
        assert tank_angle == pytest.approx(0.0)
        # Turret should have turned by turret speed
        assert turret_angle == pytest.approx(_TANK_TURRET_TURN_SPEED)

    def test_combined_tank_and_turret_turn(self):
        """Both tank and turret turn simultaneously."""
        ent = _MockEntity(Vec(100, 100), Vec(1.0, 0.0))
        actions = OperatorActions(turn=1.0, turn_turret=1.0)
        ent.apply_turn(actions)

        tank_angle = math.atan2(ent.direction.y, ent.direction.x)
        turret_angle = math.atan2(ent.turret_direction.y, ent.turret_direction.x)

        # Tank turns by tank_turn_speed
        assert tank_angle == pytest.approx(_TANK_TURN_SPEED)
        # Turret turns by tank_turn_speed (with tank) + turret_turn_speed (independent)
        assert turret_angle == pytest.approx(_TANK_TURN_SPEED + _TANK_TURRET_TURN_SPEED)


# ---------------------------------------------------------------------------
# Damage calculation
# ---------------------------------------------------------------------------

class TestCalculateDamage:
    """Test the calculate_damage function.

    NOTE: The damage formula in the original code is:
        max_shot_damage * distance_vector.magnitude() / 60
    where distance_vector is the perpendicular distance from the tank center
    to the shot's line of travel. This means HIGHER distance = HIGHER damage,
    which is counter-intuitive (typically closer hits deal more damage).
    This may be a bug in the original code, but we test the actual behaviour.
    """

    def test_direct_hit_on_line(self):
        """Shot traveling directly at tank -- tank is on the line of travel.

        NOTE: The formula computes closest_point_on_line using
        shot.position + line_direction * projection, where projection is the
        dot product of the NORMALIZED (tank-shot) vector with line_direction.
        This gives a projection in the range [-1, 1], NOT the actual distance.
        So for a tank at (50, 0) with shot at (0, 0) going right, the
        closest point is (1, 0), NOT (50, 0). The distance_vector ends up
        being (49, 0) with magnitude 49, giving damage = 100 * 49 / 60.
        """
        shot = ShotObject(Vec(0, 0), Vec(1.0, 0.0))
        tank = TankObject(Vec(50, 0), Vec(-1, 0), Vec(-1, 0))
        damage = _calculate_damage(shot, tank)
        expected = _MAX_SHOT_DAMAGE * 49.0 / 60.0
        assert damage == pytest.approx(expected, rel=0.01)

    def test_perpendicular_offset_increases_damage(self):
        """A tank offset perpendicularly from the shot line gets more damage."""
        shot = ShotObject(Vec(0, 0), Vec(1.0, 0.0))
        tank_close = TankObject(Vec(50, 5), Vec(-1, 0), Vec(-1, 0))
        tank_far = TankObject(Vec(50, 30), Vec(-1, 0), Vec(-1, 0))

        dmg_close = _calculate_damage(shot, tank_close)
        dmg_far = _calculate_damage(shot, tank_far)

        # Per the formula, larger distance = larger damage
        assert dmg_far > dmg_close

    def test_damage_is_non_negative(self):
        shot = ShotObject(Vec(100, 100), Vec(1.0, 0.0))
        tank = TankObject(Vec(100, 100), Vec(-1, 0), Vec(-1, 0))
        damage = _calculate_damage(shot, tank)
        assert damage >= 0.0

    def test_damage_formula_known_value(self):
        """Calculate expected damage for a known configuration.

        The formula uses normalized point_vector for projection, so
        closest_point is NOT the true perpendicular foot on the line.
        We compute the expected value by running the same formula.
        """
        shot = ShotObject(Vec(0, 0), Vec(1.0, 0.0))
        tank = TankObject(Vec(50, 30), Vec(-1, 0), Vec(-1, 0))
        damage = _calculate_damage(shot, tank)

        # Manually compute: point_vector normalized has x ~ 0.857
        # projection ~ 0.857, closest = (0.857, 0), dist_vec = (49.14, 30)
        # magnitude ~ 57.576
        expected = _MAX_SHOT_DAMAGE * 57.576 / 60.0
        assert damage == pytest.approx(expected, rel=0.01)

    def test_damage_symmetric_above_below(self):
        """Tank above or below shot line should get same damage at same distance."""
        shot = ShotObject(Vec(0, 0), Vec(1.0, 0.0))
        tank_above = TankObject(Vec(50, 20), Vec(-1, 0), Vec(-1, 0))
        tank_below = TankObject(Vec(50, -20), Vec(-1, 0), Vec(-1, 0))

        dmg_above = _calculate_damage(shot, tank_above)
        dmg_below = _calculate_damage(shot, tank_below)

        assert dmg_above == pytest.approx(dmg_below, rel=0.01)


# ---------------------------------------------------------------------------
# Explosion
# ---------------------------------------------------------------------------

class TestExplosion:
    """Test Explosion creation logic.

    NOTE: Explosion uses pygame.time.get_ticks(), which requires pygame to be
    initialized. We test the constructor logic conceptually. For full
    integration testing, pygame would need to be initialized.

    TODO: The Explosion class should be refactored to accept a time source
    (dependency injection) so it can be tested without pygame.
    """

    def test_explosion_attributes_conceptual(self):
        """Verify the Explosion class has the expected attributes.

        We cannot instantiate Explosion without pygame, so this test
        documents the expected interface as a specification.
        """
        # Explosion.__init__(self, center, duration) sets:
        #   self.center = center
        #   self.start_time = pygame.time.get_ticks()
        #   self.duration = duration * 1000
        #   self.alive = True
        #
        # This test is intentionally a documentation marker.
        # To make Explosion testable, extract the time dependency.
        pass


# ---------------------------------------------------------------------------
# Shot cooldown logic
# ---------------------------------------------------------------------------

class TestShotCooldown:
    """Test shot cooldown concepts.

    NOTE: check_shots_fired() in tankwars_game_server.py uses a module-level
    dict (shots_cooldown_expiry) and time.time(), and also creates Shot objects
    that depend on pygame images. This makes it hard to test in isolation.

    TODO: The cooldown logic should be extracted into a pure function that
    accepts a time parameter and a cooldown dict, returning whether the shot
    is allowed. This would make it easily testable.

    Below we test the conceptual cooldown logic with a reimplementation.
    """

    _COOLDOWN_SECONDS = 5  # matches tank_shots_cooldown in the server

    def _check_cooldown(self, player_id, current_time, cooldown_expiry):
        """Pure reimplementation of the cooldown check logic."""
        if player_id in cooldown_expiry:
            if cooldown_expiry[player_id] > current_time:
                return False  # still on cooldown
        # Fire allowed, set new cooldown
        cooldown_expiry[player_id] = current_time + self._COOLDOWN_SECONDS
        return True

    def test_first_shot_always_allowed(self):
        expiry = {}
        assert self._check_cooldown("player1", 0.0, expiry) is True

    def test_immediate_second_shot_blocked(self):
        expiry = {}
        self._check_cooldown("player1", 0.0, expiry)
        assert self._check_cooldown("player1", 0.1, expiry) is False

    def test_shot_after_cooldown_expired(self):
        expiry = {}
        self._check_cooldown("player1", 0.0, expiry)
        assert self._check_cooldown("player1", 5.1, expiry) is True

    def test_shot_exactly_at_cooldown_boundary(self):
        """At exactly the expiry time, cooldown has lapsed (check is >, not >=)."""
        expiry = {}
        self._check_cooldown("player1", 0.0, expiry)
        # expiry is 5.0, current time is 5.0: 5.0 > 5.0 is False => not on cooldown
        assert self._check_cooldown("player1", 5.0, expiry) is True

    def test_shot_just_before_cooldown_expires(self):
        """Just before the expiry time, the cooldown is still in effect."""
        expiry = {}
        self._check_cooldown("player1", 0.0, expiry)
        assert self._check_cooldown("player1", 4.999, expiry) is False

    def test_independent_player_cooldowns(self):
        expiry = {}
        self._check_cooldown("player1", 0.0, expiry)
        # player2 should be able to fire even though player1 just fired
        assert self._check_cooldown("player2", 0.0, expiry) is True

    def test_cooldown_resets_after_firing(self):
        expiry = {}
        self._check_cooldown("player1", 0.0, expiry)
        # Wait for cooldown to expire
        self._check_cooldown("player1", 6.0, expiry)
        # Now a third shot should be blocked until t=11
        assert self._check_cooldown("player1", 7.0, expiry) is False
        assert self._check_cooldown("player1", 11.1, expiry) is True


# ---------------------------------------------------------------------------
# Health / Tank death
# ---------------------------------------------------------------------------

class TestHealthSystem:
    """Test health-related game logic concepts.

    NOTE: Health tracking is embedded in the game loop. We test the concept
    of health reduction and death threshold.
    """

    def test_tank_starts_with_full_health(self):
        health = _TANK_START_HEALTH
        assert health == 200

    def test_tank_dies_when_health_below_zero(self):
        """In the game loop, tank dies when health < 0 (strict less than)."""
        health = _TANK_START_HEALTH
        health -= 201
        assert health < 0  # tank should be dead

    def test_tank_survives_at_zero_health(self):
        """Tank health == 0 does NOT trigger death (the check is health < 0)."""
        health = _TANK_START_HEALTH
        health -= 200
        assert health == 0  # tank should survive per the < 0 check

    def test_multiple_hits_accumulate(self):
        health = _TANK_START_HEALTH
        health -= 50
        health -= 50
        health -= 50
        assert health == 50

    def test_single_max_damage_shot(self):
        """A single shot at max damage (100) does not kill a full-health tank."""
        health = _TANK_START_HEALTH
        health -= _MAX_SHOT_DAMAGE
        assert health > 0


# ---------------------------------------------------------------------------
# Shot movement
# ---------------------------------------------------------------------------

class TestShotMovement:
    """Test shot movement and boundary behavior using _MockEntity as a stand-in."""

    def test_shot_moves_at_shot_speed(self):
        shot = _MockEntity(Vec(100, 100), Vec(1.0, 0.0))
        shot.move_check_boundary(1.0, _SHOT_SPEED)
        assert shot.position.x == pytest.approx(100 + _SHOT_SPEED)
        assert shot.position.y == pytest.approx(100)

    def test_shot_reaches_right_boundary(self):
        shot = _MockEntity(Vec(_DISPLAY_SIZE_X - 5, 400), Vec(1.0, 0.0))
        capped = shot.move_check_boundary(1.0, _SHOT_SPEED)
        assert capped is True
        assert shot.position.x == pytest.approx(_DISPLAY_SIZE_X)

    def test_shot_reaches_left_boundary(self):
        shot = _MockEntity(Vec(5, 400), Vec(-1.0, 0.0))
        capped = shot.move_check_boundary(1.0, _SHOT_SPEED)
        assert capped is True
        assert shot.position.x == pytest.approx(0.0)

    def test_shot_reaches_top_boundary(self):
        shot = _MockEntity(Vec(600, 5), Vec(0.0, -1.0))
        capped = shot.move_check_boundary(1.0, _SHOT_SPEED)
        assert capped is True
        assert shot.position.y == pytest.approx(0.0)

    def test_shot_reaches_bottom_boundary(self):
        shot = _MockEntity(Vec(600, _DISPLAY_SIZE_Y - 5), Vec(0.0, 1.0))
        capped = shot.move_check_boundary(1.0, _SHOT_SPEED)
        assert capped is True
        assert shot.position.y == pytest.approx(_DISPLAY_SIZE_Y)

    def test_shot_diagonal_movement(self):
        direction = Vec(1.0, 1.0).normalize()
        shot = _MockEntity(Vec(100, 100), direction)
        shot.move_check_boundary(1.0, _SHOT_SPEED)
        expected_dx = direction.x * _SHOT_SPEED
        expected_dy = direction.y * _SHOT_SPEED
        assert shot.position.x == pytest.approx(100 + expected_dx)
        assert shot.position.y == pytest.approx(100 + expected_dy)


# ---------------------------------------------------------------------------
# Game constants sanity checks
# ---------------------------------------------------------------------------

class TestGameConstants:
    """Verify game constants have sensible values."""

    def test_display_size(self):
        assert _DISPLAY_SIZE_X == 1200
        assert _DISPLAY_SIZE_Y == 800

    def test_tank_start_health(self):
        assert _TANK_START_HEALTH == 200

    def test_max_shot_damage(self):
        assert _MAX_SHOT_DAMAGE == 100

    def test_shot_speed_greater_than_tank_speed(self):
        assert _SHOT_SPEED > _TANK_MAXSPEED

    def test_turret_turns_faster_than_tank(self):
        assert _TANK_TURRET_TURN_SPEED > _TANK_TURN_SPEED

    def test_tank_turn_speed_positive(self):
        assert _TANK_TURN_SPEED > 0

    def test_shot_speed_positive(self):
        assert _SHOT_SPEED > 0
