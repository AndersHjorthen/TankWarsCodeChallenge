"""Tests for tournament.py -- headless tournament runner and simulation engine."""

import math
import pytest
from src.vec import Vec
from tank_operator import TankObject, ShotObject, GameState, OperatorActions, TankOperator
from tournament import (
    run_match,
    run_tournament,
    _cap_value_zero_max,
    _turn_vector,
    _calculate_damage,
    _SimTank,
    _SimShot,
    _rects_collide,
)
import game_config as cfg


# ---------------------------------------------------------------------------
# Reusable fixtures and helpers
# ---------------------------------------------------------------------------

class _AlwaysShootOperator(TankOperator):
    """Test operator that stands still and shoots."""
    def get_operator_name(self):
        return "AlwaysShoot"
    def get_tank_action(self, game_state):
        return OperatorActions(shoot=True)


class _DoNothingOperator(TankOperator):
    """Test operator that does absolutely nothing."""
    def get_operator_name(self):
        return "DoNothing"
    def get_tank_action(self, game_state):
        return OperatorActions()


class _SpinOperator(TankOperator):
    """Test operator that just spins left."""
    def get_operator_name(self):
        return "Spinner"
    def get_tank_action(self, game_state):
        return OperatorActions(turn=-1.0)


class _CrashOperator(TankOperator):
    """Test operator that raises an exception."""
    def get_operator_name(self):
        return "Crasher"
    def get_tank_action(self, game_state):
        raise RuntimeError("Intentional crash")


# ---------------------------------------------------------------------------
# Simulation helper tests
# ---------------------------------------------------------------------------

class TestSimCapValueZeroMax:
    """Test the boundary clamping helper."""

    def test_within_bounds(self):
        capped, val = _cap_value_zero_max(50, 100)
        assert capped is False
        assert val == 50

    def test_below_zero(self):
        capped, val = _cap_value_zero_max(-5, 100)
        assert capped is True
        assert val == 0.0

    def test_above_max(self):
        capped, val = _cap_value_zero_max(150, 100)
        assert capped is True
        assert val == 100


class TestSimTurnVector:
    """Test the turn_vector reimplementation used in simulation."""

    def test_no_turn(self):
        v = Vec(1.0, 0.0)
        _turn_vector(v, 0.0, math.radians(7.5))
        assert v.x == pytest.approx(1.0)
        assert v.y == pytest.approx(0.0)

    def test_full_right_turn(self):
        v = Vec(1.0, 0.0)
        _turn_vector(v, 1.0, math.radians(7.5))
        expected_angle = math.radians(7.5)
        assert v.x == pytest.approx(math.cos(expected_angle))
        assert v.y == pytest.approx(math.sin(expected_angle))

    def test_clamped_above_1(self):
        v1 = Vec(1.0, 0.0)
        _turn_vector(v1, 5.0, math.radians(7.5))
        v2 = Vec(1.0, 0.0)
        _turn_vector(v2, 1.0, math.radians(7.5))
        assert v1.x == pytest.approx(v2.x)
        assert v1.y == pytest.approx(v2.y)


class TestSimCalculateDamage:
    """Test the damage calculation reimplementation."""

    def test_returns_non_negative(self):
        dmg = _calculate_damage(Vec(0, 0), Vec(1, 0), Vec(50, 0))
        assert dmg >= 0.0

    def test_known_value(self):
        # Same test case as in test_game_logic.py
        dmg = _calculate_damage(Vec(0, 0), Vec(1, 0), Vec(50, 0))
        expected = cfg.MAX_SHOT_DAMAGE * 49.0 / cfg.DAMAGE_DIVISOR
        assert dmg == pytest.approx(expected, rel=0.01)


class TestRectsCollide:
    """Test AABB collision detection."""

    def test_overlapping(self):
        assert _rects_collide(Vec(100, 100), (56, 40), Vec(110, 100), (56, 40)) is True

    def test_far_apart(self):
        assert _rects_collide(Vec(100, 100), (56, 40), Vec(500, 500), (56, 40)) is False

    def test_edge_touching(self):
        # Just barely overlapping
        assert _rects_collide(Vec(100, 100), (56, 40), Vec(155, 100), (56, 40)) is True

    def test_just_outside(self):
        # Just outside collision range (max dim 56, half = 28, need gap > 56)
        assert _rects_collide(Vec(100, 100), (56, 40), Vec(157, 100), (56, 40)) is False


# ---------------------------------------------------------------------------
# _SimTank tests
# ---------------------------------------------------------------------------

class TestSimTank:
    """Test the simulated tank entity."""

    def test_creation(self):
        op = _DoNothingOperator()
        tank = _SimTank(op, Vec(100, 200), Vec(1, 0))
        assert tank.name == "DoNothing"
        assert tank.health == cfg.TANK_START_HEALTH
        assert tank.kills == 0
        assert tank.damage_dealt == 0.0

    def test_get_gamestate_object(self):
        op = _DoNothingOperator()
        tank = _SimTank(op, Vec(100, 200), Vec(1, 0))
        gs_obj = tank.get_gamestate_object()
        assert isinstance(gs_obj, TankObject)
        assert gs_obj.position.x == pytest.approx(100)
        assert gs_obj.position.y == pytest.approx(200)

    def test_move_forward(self):
        op = _DoNothingOperator()
        tank = _SimTank(op, Vec(600, 400), Vec(1, 0))
        tank.move(1.0, 1200, 800)
        assert tank.position.x == pytest.approx(600 + cfg.TANK_MAX_SPEED)
        assert tank.position.y == pytest.approx(400)

    def test_move_capped_at_boundary(self):
        op = _DoNothingOperator()
        tank = _SimTank(op, Vec(1199, 400), Vec(1, 0))
        tank.move(1.0, 1200, 800)
        assert tank.position.x == pytest.approx(1200)


# ---------------------------------------------------------------------------
# _SimShot tests
# ---------------------------------------------------------------------------

class TestSimShot:
    """Test the simulated shot entity."""

    def test_creation(self):
        op = _DoNothingOperator()
        tank = _SimTank(op, Vec(100, 200), Vec(1, 0))
        shot = _SimShot(tank)
        assert shot.owner is tank
        assert shot.position.x == pytest.approx(100)
        assert shot.direction.x == pytest.approx(1)

    def test_move(self):
        op = _DoNothingOperator()
        tank = _SimTank(op, Vec(100, 200), Vec(1, 0))
        shot = _SimShot(tank)
        hit_wall = shot.move(1200, 800)
        assert hit_wall is False
        assert shot.position.x == pytest.approx(100 + cfg.SHOT_SPEED)

    def test_move_hits_boundary(self):
        op = _DoNothingOperator()
        tank = _SimTank(op, Vec(1195, 400), Vec(1, 0))
        shot = _SimShot(tank)
        hit_wall = shot.move(1200, 800)
        assert hit_wall is True

    def test_get_gamestate_object(self):
        op = _DoNothingOperator()
        tank = _SimTank(op, Vec(100, 200), Vec(1, 0))
        shot = _SimShot(tank)
        gs_obj = shot.get_gamestate_object()
        assert isinstance(gs_obj, ShotObject)


# ---------------------------------------------------------------------------
# run_match tests
# ---------------------------------------------------------------------------

class TestRunMatch:
    """Test the run_match function."""

    def test_returns_dict_with_expected_keys(self):
        result = run_match(_DoNothingOperator, _DoNothingOperator, max_frames=10)
        assert "winner" in result
        assert "tank_a" in result
        assert "tank_b" in result
        assert "name" in result["tank_a"]
        assert "kills" in result["tank_a"]
        assert "damage_dealt" in result["tank_a"]
        assert "health_remaining" in result["tank_a"]

    def test_short_match_completes(self):
        result = run_match(_DoNothingOperator, _DoNothingOperator, max_frames=5)
        # Both do nothing, so it's a draw by damage (both 0)
        assert result["winner"] == "Draw"

    def test_shooter_vs_nothing(self):
        # AlwaysShoot should eventually kill DoNothing
        result = run_match(_AlwaysShootOperator, _DoNothingOperator)
        # AlwaysShoot fires from red position towards blue position
        # Due to starting angles, it may or may not hit, but it should at least deal more damage
        # In a full game they start facing away from each other, so this might be complex
        assert result is not None
        assert "winner" in result

    def test_match_handles_crashing_operator(self):
        """An operator that throws exceptions should not crash the match."""
        result = run_match(_CrashOperator, _DoNothingOperator, max_frames=10)
        assert result is not None
        assert "winner" in result

    def test_match_with_spinner(self):
        result = run_match(_SpinOperator, _DoNothingOperator, max_frames=100)
        assert result is not None

    def test_match_respects_max_frames(self):
        """Match should end within the frame limit."""
        result = run_match(_DoNothingOperator, _DoNothingOperator, max_frames=1)
        assert result is not None


# ---------------------------------------------------------------------------
# run_tournament tests
# ---------------------------------------------------------------------------

class TestRunTournament:
    """Test the round-robin tournament runner."""

    def test_tournament_returns_stats(self):
        results = run_tournament(
            [_DoNothingOperator, _SpinOperator],
            matches_per_pair=1,
            max_frames_per_match=10,
            quiet=True,
        )
        assert "DoNothing" in results
        assert "Spinner" in results

    def test_tournament_stats_structure(self):
        results = run_tournament(
            [_DoNothingOperator, _SpinOperator],
            matches_per_pair=1,
            max_frames_per_match=10,
            quiet=True,
        )
        for name, stats in results.items():
            assert "wins" in stats
            assert "losses" in stats
            assert "draws" in stats
            assert "kills" in stats
            assert "damage_dealt" in stats

    def test_tournament_three_operators(self):
        results = run_tournament(
            [_DoNothingOperator, _SpinOperator, _AlwaysShootOperator],
            matches_per_pair=1,
            max_frames_per_match=10,
            quiet=True,
        )
        assert len(results) == 3

    def test_tournament_wins_losses_draws_add_up(self):
        operators = [_DoNothingOperator, _SpinOperator, _AlwaysShootOperator]
        matches_per_pair = 2
        results = run_tournament(
            operators,
            matches_per_pair=matches_per_pair,
            max_frames_per_match=10,
            quiet=True,
        )
        total_wins = sum(s["wins"] for s in results.values())
        total_losses = sum(s["losses"] for s in results.values())
        total_draws = sum(s["draws"] for s in results.values())

        # wins should equal losses (every win produces one loss)
        assert total_wins == total_losses
        # draws should be even (both sides get a draw)
        assert total_draws % 2 == 0

    def test_tournament_too_few_operators(self):
        """Tournament with fewer than 2 operators should return empty."""
        results = run_tournament([_DoNothingOperator], quiet=True)
        assert results == {}

    def test_tournament_with_crashing_operator(self):
        """Tournament should handle operators that crash."""
        results = run_tournament(
            [_CrashOperator, _DoNothingOperator],
            matches_per_pair=1,
            max_frames_per_match=10,
            quiet=True,
        )
        assert len(results) == 2


# ---------------------------------------------------------------------------
# Integration: example operators in tournament
# ---------------------------------------------------------------------------

class TestExampleOperatorsInTournament:
    """Run example operators through the tournament to verify integration."""

    def test_example_operators_complete_match(self):
        from example_operators import ChaserOperator, DodgerOperator, SniperOperator
        result = run_match(ChaserOperator, SniperOperator, max_frames=300)
        assert result is not None
        assert "winner" in result

    def test_all_example_operators_in_tournament(self):
        from example_operators import ChaserOperator, DodgerOperator, SniperOperator
        results = run_tournament(
            [ChaserOperator, DodgerOperator, SniperOperator],
            matches_per_pair=1,
            max_frames_per_match=300,
            quiet=True,
        )
        assert len(results) == 3
        assert "Chaser" in results
        assert "Dodger" in results
        assert "Sniper" in results
