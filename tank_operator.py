# -*- coding: utf-8 -*-
from __future__ import annotations

from src.vec import Vec
# Vec is a 2D vector with member attributes x and y.

class TankObject:
    def __init__(self, position: Vec, direction: Vec, turret_direction: Vec) -> None:
        """
        Represents a Tank in the game.

        :param position: 2D Vector representing the tanks position on the game field.
        :param direction: 2D Vector representing the tanks facing direction.
        :param turret_direction: 2D Vector representing the turrets facing direction.
        """
        self.position: Vec = position
        self.direction: Vec = direction
        self.turret_direction: Vec = turret_direction

class ShotObject:
    def __init__(self, position: Vec, direction: Vec) -> None:
        """
        Represents a Shot in the game.

        :param position: 2D Vector representing the shots position on the game field.
        :param direction: 2D Vector representing the shots facing direction.
        """
        self.position: Vec = position
        self.direction: Vec = direction

class ObstacleObject:
    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        """
        Represents an obstacle/wall in the arena.

        :param x: X coordinate of the top-left corner.
        :param y: Y coordinate of the top-left corner.
        :param width: Width of the obstacle in pixels.
        :param height: Height of the obstacle in pixels.
        """
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height

class PowerUpObject:
    def __init__(self, x: float, y: float, power_type: str) -> None:
        """
        Represents a visible power-up in the arena.

        :param x: X coordinate of the power-up center.
        :param y: Y coordinate of the power-up center.
        :param power_type: String type - one of "speed_boost", "rapid_fire", "shield".
        """
        self.x: float = x
        self.y: float = y
        self.power_type: str = power_type

class GameState:
    def __init__(self, tank: TankObject, other_tanks: list[TankObject] | None = None,
                 shots: list[ShotObject] | None = None,
                 obstacles: list[ObstacleObject] | None = None,
                 powerups: list[PowerUpObject] | None = None,
                 my_health: float | None = None,
                 arena_width: float | None = None,
                 arena_height: float | None = None,
                 game_time_remaining: float | None = None) -> None:
        """
        Holds the current state of the game, providing necessary information for decision-making.

        :param tank: TankObject representing the player's own tank.
        :param other_tanks: List of TankObject representing other tanks in the game.
        :param shots: List of ShotObject representing shots currently active in the game.
        :param obstacles: List of ObstacleObject representing walls/obstacles in the arena.
        :param powerups: List of PowerUpObject representing collectible power-ups on the field.
        :param my_health: Current health of the player's tank (0-200).
        :param arena_width: Width of the game arena in pixels.
        :param arena_height: Height of the game arena in pixels.
        :param game_time_remaining: Seconds remaining in the current game.
        """
        self.tank: TankObject = tank
        self.other_tanks: list[TankObject] = other_tanks if other_tanks is not None else []
        self.shots: list[ShotObject] = shots if shots is not None else []
        self.obstacles: list[ObstacleObject] | None = obstacles
        self.powerups: list[PowerUpObject] | None = powerups
        self.my_health: float | None = my_health
        self.arena_width: float | None = arena_width
        self.arena_height: float | None = arena_height
        self.game_time_remaining: float | None = game_time_remaining

class OperatorActions:
    def __init__(self, turn: float = 0.0, turn_turret: float = 0.0,
                 engine: float = 0.0, shoot: bool = False) -> None:
        """
        Encapsulates the actions that a tank operator can take in a given frame.
        """
        self.turn: float = turn    # [-1.0 to 1.0] left to right respectively.
        self.turn_turret: float = turn_turret    # [-1.0 to 1.0] left to right respectively.
        self.engine: float = engine  # [-1.0 to 1.0] reverse to full ahead.
        self.shoot: bool = shoot  # Set to True to fire cannon!

class TankOperator:
    def get_tank_action(self, game_state: GameState) -> OperatorActions:
        """
        This method should be implemented by the user to define the tank's actions based on the game state.

        :param game_state: GameState instance containing information about the current state of the game.
        :return: OperatorActions instance representing the tank's actions for the current frame.
        """
        raise NotImplementedError("This method should be overridden in a subclass")

    def get_operator_name(self) -> str:
        """
        Returns the name of the operator.

        :return: String representing the operator's name.
        """
        raise NotImplementedError("This method should be overridden in a subclass")
