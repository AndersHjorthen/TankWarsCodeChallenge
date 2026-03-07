"""Tests for example_operators.py -- ChaserOperator, DodgerOperator, SniperOperator."""

import math
import pytest
from src.vec import Vec
from tank_operator import TankObject, ShotObject, GameState, OperatorActions, TankOperator
from example_operators import (
    ChaserOperator,
    DodgerOperator,
    SniperOperator,
    _angle_between,
    _find_nearest_enemy,
    _turn_signal,
    _proportional_turn,
)


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestAngleBetween:
    """Tests for the _angle_between helper."""

    def test_same_direction_zero_angle(self):
        assert _angle_between(Vec(1, 0), Vec(1, 0)) == pytest.approx(0.0)

    def test_right_angle_positive(self):
        # From (1,0) to (0,1) is +90 degrees = pi/2
        assert _angle_between(Vec(1, 0), Vec(0, 1)) == pytest.approx(math.pi / 2)

    def test_right_angle_negative(self):
        # From (1,0) to (0,-1) is -90 degrees = -pi/2
        assert _angle_between(Vec(1, 0), Vec(0, -1)) == pytest.approx(-math.pi / 2)

    def test_opposite_direction(self):
        result = _angle_between(Vec(1, 0), Vec(-1, 0))
        assert abs(result) == pytest.approx(math.pi)

    def test_small_positive_angle(self):
        # Slightly rotated clockwise in pygame coords (+y down)
        angle = math.radians(10)
        target = Vec(math.cos(angle), math.sin(angle))
        assert _angle_between(Vec(1, 0), target) == pytest.approx(angle, abs=1e-6)

    def test_small_negative_angle(self):
        angle = math.radians(-10)
        target = Vec(math.cos(angle), math.sin(angle))
        assert _angle_between(Vec(1, 0), target) == pytest.approx(angle, abs=1e-6)

    def test_wraps_correctly(self):
        # The result should always be in (-pi, pi]
        result = _angle_between(Vec(-1, 0.01), Vec(-1, -0.01))
        assert -math.pi < result <= math.pi


class TestFindNearestEnemy:
    """Tests for the _find_nearest_enemy helper."""

    def test_no_enemies_returns_none(self):
        assert _find_nearest_enemy(Vec(100, 100), []) is None

    def test_single_enemy(self):
        enemy = TankObject(Vec(200, 200), Vec(1, 0), Vec(1, 0))
        result = _find_nearest_enemy(Vec(100, 100), [enemy])
        assert result is enemy

    def test_picks_closest(self):
        close = TankObject(Vec(110, 100), Vec(1, 0), Vec(1, 0))
        far = TankObject(Vec(900, 900), Vec(1, 0), Vec(1, 0))
        result = _find_nearest_enemy(Vec(100, 100), [far, close])
        assert result is close

    def test_three_enemies(self):
        e1 = TankObject(Vec(200, 200), Vec(1, 0), Vec(1, 0))
        e2 = TankObject(Vec(105, 100), Vec(1, 0), Vec(1, 0))
        e3 = TankObject(Vec(500, 500), Vec(1, 0), Vec(1, 0))
        result = _find_nearest_enemy(Vec(100, 100), [e1, e2, e3])
        assert result is e2


class TestTurnSignal:
    """Tests for the _turn_signal helper."""

    def test_positive_angle_returns_positive(self):
        assert _turn_signal(0.5) == 1.0

    def test_negative_angle_returns_negative(self):
        assert _turn_signal(-0.5) == -1.0

    def test_zero_angle_returns_zero(self):
        assert _turn_signal(0.0) == 0.0

    def test_within_threshold_returns_zero(self):
        assert _turn_signal(0.01, threshold=0.05) == 0.0

    def test_outside_threshold_returns_signal(self):
        assert _turn_signal(0.1, threshold=0.05) == 1.0


class TestProportionalTurn:
    """Tests for the _proportional_turn helper."""

    def test_zero_angle_returns_zero(self):
        assert _proportional_turn(0.0) == pytest.approx(0.0)

    def test_clamped_to_1(self):
        # Large angle should clamp to 1.0
        assert _proportional_turn(math.pi) == pytest.approx(1.0)

    def test_clamped_to_neg1(self):
        assert _proportional_turn(-math.pi) == pytest.approx(-1.0)

    def test_proportional_small_angle(self):
        # Half the max turn speed should give 0.5
        half = math.radians(7.5) / 2.0
        assert _proportional_turn(half) == pytest.approx(0.5)

    def test_zero_max_speed_returns_zero(self):
        assert _proportional_turn(1.0, max_turn_speed_rad=0.0) == 0.0


# ---------------------------------------------------------------------------
# Operator base class compliance
# ---------------------------------------------------------------------------

class TestOperatorInheritance:
    """All example operators should inherit from TankOperator."""

    def test_chaser_is_tank_operator(self):
        assert issubclass(ChaserOperator, TankOperator)

    def test_dodger_is_tank_operator(self):
        assert issubclass(DodgerOperator, TankOperator)

    def test_sniper_is_tank_operator(self):
        assert issubclass(SniperOperator, TankOperator)


class TestOperatorNames:
    """Each operator should return a meaningful name."""

    def test_chaser_name(self):
        assert ChaserOperator().get_operator_name() == "Chaser"

    def test_dodger_name(self):
        assert DodgerOperator().get_operator_name() == "Dodger"

    def test_sniper_name(self):
        assert SniperOperator().get_operator_name() == "Sniper"


# ---------------------------------------------------------------------------
# ChaserOperator behavior tests
# ---------------------------------------------------------------------------

class TestChaserOperator:
    """Test ChaserOperator decision-making."""

    def _make_game_state(self, my_pos, my_dir, enemies=None, shots=None):
        tank = TankObject(my_pos, my_dir, Vec(my_dir))
        if enemies is None:
            enemies = []
        return GameState(
            tank,
            other_tanks=enemies,
            shots=shots or [],
        )

    def test_returns_operator_actions(self):
        gs = self._make_game_state(
            Vec(100, 100), Vec(1, 0),
            enemies=[TankObject(Vec(500, 500), Vec(-1, 0), Vec(-1, 0))],
        )
        actions = ChaserOperator().get_tank_action(gs)
        assert isinstance(actions, OperatorActions)

    def test_spins_when_no_enemies(self):
        gs = self._make_game_state(Vec(100, 100), Vec(1, 0))
        actions = ChaserOperator().get_tank_action(gs)
        assert actions.turn != 0.0

    def test_drives_forward_towards_enemy(self):
        # Enemy is directly ahead
        gs = self._make_game_state(
            Vec(100, 100), Vec(1, 0),
            enemies=[TankObject(Vec(500, 100), Vec(-1, 0), Vec(-1, 0))],
        )
        actions = ChaserOperator().get_tank_action(gs)
        assert actions.engine > 0

    def test_shoots_when_turret_aligned(self):
        # Enemy is directly in the turret's line of fire
        gs = self._make_game_state(
            Vec(100, 100), Vec(1, 0),
            enemies=[TankObject(Vec(500, 100), Vec(-1, 0), Vec(-1, 0))],
        )
        actions = ChaserOperator().get_tank_action(gs)
        # Turret faces (1,0), enemy at (500,100) - same y, so aligned
        assert actions.shoot is True

    def test_turns_towards_enemy_not_ahead(self):
        # Enemy is 90 degrees to the right (below in pygame coords)
        gs = self._make_game_state(
            Vec(100, 100), Vec(1, 0),
            enemies=[TankObject(Vec(100, 500), Vec(0, -1), Vec(0, -1))],
        )
        actions = ChaserOperator().get_tank_action(gs)
        # Should turn right (positive turn value) since enemy is below
        assert actions.turn > 0

    def test_does_not_shoot_when_not_aligned(self):
        # Enemy is behind us
        gs = self._make_game_state(
            Vec(500, 100), Vec(1, 0),
            enemies=[TankObject(Vec(100, 100), Vec(1, 0), Vec(1, 0))],
        )
        actions = ChaserOperator().get_tank_action(gs)
        # Turret faces (1,0), enemy is at x=100 which is behind us
        assert actions.shoot is False


# ---------------------------------------------------------------------------
# DodgerOperator behavior tests
# ---------------------------------------------------------------------------

class TestDodgerOperator:
    """Test DodgerOperator decision-making."""

    def _make_game_state(self, my_pos, my_dir, enemies=None, shots=None):
        tank = TankObject(my_pos, my_dir, Vec(my_dir))
        return GameState(
            tank,
            other_tanks=enemies or [],
            shots=shots or [],
        )

    def test_returns_operator_actions(self):
        gs = self._make_game_state(Vec(600, 400), Vec(1, 0))
        actions = DodgerOperator().get_tank_action(gs)
        assert isinstance(actions, OperatorActions)

    def test_dodges_incoming_shot(self):
        # Shot heading directly at us from a close range (within THREAT_DISTANCE=300)
        shot = ShotObject(Vec(400, 400), Vec(1, 0))  # heading right towards (600,400)
        gs = self._make_game_state(
            Vec(600, 400), Vec(1, 0),
            shots=[shot],
        )
        actions = DodgerOperator().get_tank_action(gs)
        # Should be driving at full speed to dodge
        assert actions.engine == pytest.approx(1.0)

    def test_ignores_shot_moving_away(self):
        # Shot heading away from us
        shot = ShotObject(Vec(200, 400), Vec(-1, 0))  # heading left, away
        enemy = TankObject(Vec(800, 400), Vec(-1, 0), Vec(-1, 0))
        gs = self._make_game_state(
            Vec(600, 400), Vec(1, 0),
            enemies=[enemy],
            shots=[shot],
        )
        actions = DodgerOperator().get_tank_action(gs)
        # Should be in patrol mode, not full-speed dodge
        assert actions.engine < 1.0

    def test_spins_when_no_enemies_or_shots(self):
        gs = self._make_game_state(Vec(600, 400), Vec(1, 0))
        actions = DodgerOperator().get_tank_action(gs)
        # No enemies, so spins to search
        assert actions.turn != 0.0

    def test_ignores_distant_shots(self):
        # Shot is very far away
        shot = ShotObject(Vec(10, 10), Vec(1, 0))
        enemy = TankObject(Vec(800, 400), Vec(-1, 0), Vec(-1, 0))
        gs = self._make_game_state(
            Vec(600, 400), Vec(1, 0),
            enemies=[enemy],
            shots=[shot],
        )
        actions = DodgerOperator().get_tank_action(gs)
        # Should be in patrol mode, not dodge mode
        assert actions.engine < 1.0


# ---------------------------------------------------------------------------
# SniperOperator behavior tests
# ---------------------------------------------------------------------------

class TestSniperOperator:
    """Test SniperOperator decision-making."""

    def _make_game_state(self, my_pos, my_dir, enemies=None, shots=None,
                         my_health=None, arena_w=None, arena_h=None):
        tank = TankObject(my_pos, my_dir, Vec(my_dir))
        return GameState(
            tank,
            other_tanks=enemies or [],
            shots=shots or [],
            my_health=my_health,
            arena_width=arena_w,
            arena_height=arena_h,
        )

    def test_returns_operator_actions(self):
        gs = self._make_game_state(Vec(600, 400), Vec(1, 0))
        actions = SniperOperator().get_tank_action(gs)
        assert isinstance(actions, OperatorActions)

    def test_scans_when_no_enemies(self):
        gs = self._make_game_state(Vec(600, 400), Vec(1, 0))
        actions = SniperOperator().get_tank_action(gs)
        assert actions.turn_turret != 0.0

    def test_stays_mostly_still(self):
        # Enemy at moderate distance, directly ahead
        enemy = TankObject(Vec(900, 400), Vec(-1, 0), Vec(-1, 0))
        gs = self._make_game_state(
            Vec(600, 400), Vec(1, 0), enemies=[enemy]
        )
        actions = SniperOperator().get_tank_action(gs)
        # Sniper should barely move
        assert abs(actions.engine) < 0.2

    def test_shoots_when_perfectly_aligned(self):
        # Enemy is directly ahead at turret direction
        enemy = TankObject(Vec(900, 400), Vec(-1, 0), Vec(-1, 0))
        gs = self._make_game_state(
            Vec(600, 400), Vec(1, 0), enemies=[enemy]
        )
        actions = SniperOperator().get_tank_action(gs)
        # Turret faces (1,0), enemy at (900,400) is directly ahead
        assert actions.shoot is True

    def test_does_not_shoot_when_misaligned(self):
        # Enemy is at a large angle from turret direction
        enemy = TankObject(Vec(600, 100), Vec(0, 1), Vec(0, 1))
        gs = self._make_game_state(
            Vec(600, 400), Vec(1, 0), enemies=[enemy]
        )
        actions = SniperOperator().get_tank_action(gs)
        # Enemy is directly above, turret faces right -- not aligned
        assert actions.shoot is False

    def test_retreats_when_health_low(self):
        enemy = TankObject(Vec(700, 400), Vec(-1, 0), Vec(-1, 0))
        gs = self._make_game_state(
            Vec(600, 400), Vec(1, 0),
            enemies=[enemy],
            my_health=30.0,  # below LOW_HEALTH_THRESHOLD of 80
        )
        actions = SniperOperator().get_tank_action(gs)
        # Should retreat (reverse) since enemy is roughly ahead
        assert actions.engine < 0

    def test_retreats_when_enemy_too_close(self):
        enemy = TankObject(Vec(650, 400), Vec(-1, 0), Vec(-1, 0))
        gs = self._make_game_state(
            Vec(600, 400), Vec(1, 0), enemies=[enemy]
        )
        actions = SniperOperator().get_tank_action(gs)
        # Enemy is within RETREAT_DISTANCE (150), should retreat
        assert actions.engine < 0

    def test_moves_to_center_when_near_wall(self):
        # Tank in corner with arena dimensions provided
        enemy = TankObject(Vec(600, 400), Vec(-1, 0), Vec(-1, 0))
        gs = self._make_game_state(
            Vec(10, 10), Vec(-1, -1),
            enemies=[enemy],
            arena_w=1200.0, arena_h=800.0,
        )
        actions = SniperOperator().get_tank_action(gs)
        # Should try to move towards center, so engine > 0
        assert actions.engine > 0


# ---------------------------------------------------------------------------
# Robustness tests
# ---------------------------------------------------------------------------

class TestOperatorRobustness:
    """Test that operators handle edge cases gracefully."""

    @pytest.mark.parametrize("operator_cls", [ChaserOperator, DodgerOperator, SniperOperator])
    def test_handles_empty_game_state(self, operator_cls):
        """Operators should not crash with no enemies and no shots."""
        tank = TankObject(Vec(100, 100), Vec(1, 0), Vec(1, 0))
        gs = GameState(tank)
        actions = operator_cls().get_tank_action(gs)
        assert isinstance(actions, OperatorActions)

    @pytest.mark.parametrize("operator_cls", [ChaserOperator, DodgerOperator, SniperOperator])
    def test_handles_many_enemies(self, operator_cls):
        """Operators should handle multiple enemies without errors."""
        tank = TankObject(Vec(100, 100), Vec(1, 0), Vec(1, 0))
        enemies = [
            TankObject(Vec(200 + i * 100, 200 + i * 50), Vec(-1, 0), Vec(-1, 0))
            for i in range(10)
        ]
        gs = GameState(tank, other_tanks=enemies)
        actions = operator_cls().get_tank_action(gs)
        assert isinstance(actions, OperatorActions)

    @pytest.mark.parametrize("operator_cls", [ChaserOperator, DodgerOperator, SniperOperator])
    def test_handles_many_shots(self, operator_cls):
        """Operators should handle many active shots without errors."""
        tank = TankObject(Vec(600, 400), Vec(1, 0), Vec(1, 0))
        shots = [
            ShotObject(Vec(i * 50, i * 50), Vec(1, 0))
            for i in range(20)
        ]
        gs = GameState(tank, shots=shots)
        actions = operator_cls().get_tank_action(gs)
        assert isinstance(actions, OperatorActions)

    @pytest.mark.parametrize("operator_cls", [ChaserOperator, DodgerOperator, SniperOperator])
    def test_actions_values_in_range(self, operator_cls):
        """All action values should be in valid ranges."""
        tank = TankObject(Vec(600, 400), Vec(1, 0), Vec(1, 0))
        enemy = TankObject(Vec(800, 400), Vec(-1, 0), Vec(-1, 0))
        shot = ShotObject(Vec(300, 400), Vec(1, 0))
        gs = GameState(
            tank, other_tanks=[enemy], shots=[shot],
            my_health=100.0, arena_width=1200.0, arena_height=800.0,
        )
        actions = operator_cls().get_tank_action(gs)

        assert -1.0 <= actions.turn <= 1.0
        assert -1.0 <= actions.turn_turret <= 1.0
        assert -1.0 <= actions.engine <= 1.0
        assert isinstance(actions.shoot, bool)

    @pytest.mark.parametrize("operator_cls", [ChaserOperator, DodgerOperator, SniperOperator])
    def test_works_without_enriched_fields(self, operator_cls):
        """Operators should work fine when enriched GameState fields are None."""
        tank = TankObject(Vec(600, 400), Vec(1, 0), Vec(1, 0))
        enemy = TankObject(Vec(800, 400), Vec(-1, 0), Vec(-1, 0))
        gs = GameState(tank, other_tanks=[enemy])
        # my_health, arena_width, arena_height, game_time_remaining are all None
        actions = operator_cls().get_tank_action(gs)
        assert isinstance(actions, OperatorActions)
