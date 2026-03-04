"""Common fixtures for TankWars test suite."""

import sys
import os
import pytest

# Ensure the project root is on sys.path so imports work correctly.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.vec import Vec
from tank_operator import TankObject, ShotObject, GameState, OperatorActions


@pytest.fixture
def sample_tank():
    """A TankObject at a known position facing right with turret facing right."""
    return TankObject(
        position=Vec(100.0, 200.0),
        direction=Vec(1.0, 0.0),
        turret_direction=Vec(1.0, 0.0),
    )


@pytest.fixture
def sample_enemy_tank():
    """An enemy TankObject at a different position."""
    return TankObject(
        position=Vec(500.0, 300.0),
        direction=Vec(-1.0, 0.0),
        turret_direction=Vec(-1.0, 0.0),
    )


@pytest.fixture
def sample_shot():
    """A ShotObject moving to the right from a known position."""
    return ShotObject(
        position=Vec(200.0, 200.0),
        direction=Vec(1.0, 0.0),
    )


@pytest.fixture
def sample_game_state(sample_tank, sample_enemy_tank, sample_shot):
    """A GameState with one player tank, one enemy, and one shot."""
    return GameState(
        tank=sample_tank,
        other_tanks=[sample_enemy_tank],
        shots=[sample_shot],
    )


@pytest.fixture
def sample_operator_actions():
    """Default OperatorActions with no input."""
    return OperatorActions()
