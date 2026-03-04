"""Tests for tank_operator.py -- GameState, TankObject, ShotObject, OperatorActions."""

import pytest
from src.vec import Vec
from tank_operator import (
    TankObject,
    ShotObject,
    GameState,
    OperatorActions,
    TankOperator,
)


# ---------------------------------------------------------------------------
# TankObject
# ---------------------------------------------------------------------------

class TestTankObject:
    def test_construction(self):
        pos = Vec(10.0, 20.0)
        dir_ = Vec(1.0, 0.0)
        turret = Vec(0.0, 1.0)
        tank = TankObject(pos, dir_, turret)
        assert tank.position is pos
        assert tank.direction is dir_
        assert tank.turret_direction is turret

    def test_attributes_match(self):
        tank = TankObject(Vec(1.0, 2.0), Vec(3.0, 4.0), Vec(5.0, 6.0))
        assert tank.position.x == 1.0
        assert tank.position.y == 2.0
        assert tank.direction.x == 3.0
        assert tank.direction.y == 4.0
        assert tank.turret_direction.x == 5.0
        assert tank.turret_direction.y == 6.0

    def test_serialization_via_dict(self):
        """TankObject attributes should be accessible as expected for JSON serialization."""
        tank = TankObject(Vec(10.0, 20.0), Vec(1.0, 0.0), Vec(0.0, 1.0))
        d = tank.__dict__
        assert "position" in d
        assert "direction" in d
        assert "turret_direction" in d


# ---------------------------------------------------------------------------
# ShotObject
# ---------------------------------------------------------------------------

class TestShotObject:
    def test_construction(self):
        pos = Vec(100.0, 200.0)
        dir_ = Vec(0.0, -1.0)
        shot = ShotObject(pos, dir_)
        assert shot.position is pos
        assert shot.direction is dir_

    def test_attributes_match(self):
        shot = ShotObject(Vec(5.0, 10.0), Vec(-1.0, 0.0))
        assert shot.position.x == 5.0
        assert shot.position.y == 10.0
        assert shot.direction.x == -1.0
        assert shot.direction.y == 0.0

    def test_serialization_via_dict(self):
        shot = ShotObject(Vec(1.0, 2.0), Vec(3.0, 4.0))
        d = shot.__dict__
        assert "position" in d
        assert "direction" in d


# ---------------------------------------------------------------------------
# GameState
# ---------------------------------------------------------------------------

class TestGameState:
    def test_construction_defaults(self):
        tank = TankObject(Vec(0, 0), Vec(1, 0), Vec(1, 0))
        gs = GameState(tank)
        assert gs.tank is tank
        # Default lists - note: the mutable default argument is a known
        # Python gotcha in the original code, but we test the behaviour as-is.
        assert isinstance(gs.other_tanks, list)
        assert isinstance(gs.shots, list)

    def test_construction_with_provided_tanks_and_shots(self, sample_game_state):
        gs = sample_game_state
        assert gs.tank is not None
        assert len(gs.other_tanks) == 1
        assert len(gs.shots) == 1

    def test_tank_reference(self, sample_tank):
        gs = GameState(sample_tank)
        assert gs.tank is sample_tank

    def test_other_tanks_populated(self, sample_tank, sample_enemy_tank):
        gs = GameState(sample_tank, other_tanks=[sample_enemy_tank])
        assert len(gs.other_tanks) == 1
        assert gs.other_tanks[0] is sample_enemy_tank

    def test_shots_populated(self, sample_tank, sample_shot):
        gs = GameState(sample_tank, shots=[sample_shot])
        assert len(gs.shots) == 1
        assert gs.shots[0] is sample_shot

    def test_multiple_enemies(self):
        tank = TankObject(Vec(0, 0), Vec(1, 0), Vec(1, 0))
        enemies = [
            TankObject(Vec(100, 100), Vec(-1, 0), Vec(-1, 0)),
            TankObject(Vec(200, 200), Vec(0, 1), Vec(0, 1)),
            TankObject(Vec(300, 300), Vec(0, -1), Vec(0, -1)),
        ]
        gs = GameState(tank, other_tanks=enemies)
        assert len(gs.other_tanks) == 3

    def test_multiple_shots(self):
        tank = TankObject(Vec(0, 0), Vec(1, 0), Vec(1, 0))
        shots = [
            ShotObject(Vec(50, 50), Vec(1, 0)),
            ShotObject(Vec(150, 150), Vec(0, 1)),
        ]
        gs = GameState(tank, shots=shots)
        assert len(gs.shots) == 2


# ---------------------------------------------------------------------------
# OperatorActions
# ---------------------------------------------------------------------------

class TestOperatorActions:
    def test_default_values(self):
        actions = OperatorActions()
        assert actions.turn == 0.0
        assert actions.turn_turret == 0.0
        assert actions.engine == 0.0
        assert actions.shoot is False

    def test_custom_values(self):
        actions = OperatorActions(turn=0.5, turn_turret=-0.3, engine=1.0, shoot=True)
        assert actions.turn == 0.5
        assert actions.turn_turret == -0.3
        assert actions.engine == 1.0
        assert actions.shoot is True

    def test_max_values(self):
        actions = OperatorActions(turn=1.0, turn_turret=1.0, engine=1.0, shoot=True)
        assert actions.turn == 1.0
        assert actions.turn_turret == 1.0
        assert actions.engine == 1.0

    def test_min_values(self):
        actions = OperatorActions(turn=-1.0, turn_turret=-1.0, engine=-1.0, shoot=False)
        assert actions.turn == -1.0
        assert actions.turn_turret == -1.0
        assert actions.engine == -1.0

    def test_out_of_range_values_not_clamped_at_construction(self):
        """OperatorActions does not clamp at construction time. Clamping
        happens in the game server's turn_vector and move_check_boundary."""
        actions = OperatorActions(turn=5.0, engine=-10.0)
        assert actions.turn == 5.0
        assert actions.engine == -10.0

    def test_serialization_via_dict(self):
        actions = OperatorActions(turn=0.5, shoot=True)
        d = actions.__dict__
        assert d["turn"] == 0.5
        assert d["shoot"] is True
        assert "turn_turret" in d
        assert "engine" in d

    def test_fixture_defaults(self, sample_operator_actions):
        assert sample_operator_actions.turn == 0.0
        assert sample_operator_actions.engine == 0.0
        assert sample_operator_actions.shoot is False


# ---------------------------------------------------------------------------
# TankOperator base class
# ---------------------------------------------------------------------------

class TestTankOperator:
    def test_get_tank_action_not_implemented(self):
        op = TankOperator()
        with pytest.raises(NotImplementedError):
            op.get_tank_action(None)

    def test_get_operator_name_not_implemented(self):
        op = TankOperator()
        with pytest.raises(NotImplementedError):
            op.get_operator_name()
