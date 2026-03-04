# -*- coding: utf-8 -*-

from src.vec import Vec
# Vec is a 2D vector with member attributes x and y.

class TankObject:
    def __init__(self, position, direction, turret_direction):
        """
        Represents a Tank in the game.

        :param position: 2D Vector representing the tanks position on the game field. (Check out the Vec class in src/vec.py)
        :param direction: 2D Vector representing the tanks facing direction.
        :param turret_direction: 2D Vector representing the turrets facing direction.
        """
        self.position = position
        self.direction = direction
        self.turret_direction = turret_direction

class ShotObject:
    def __init__(self, position, direction):
        """
        Represents a Tank in the game.

        :param position: 2D Vector representing the shots position on the game field. (Check out the Vec class in src/vec.py)
        :param direction: 2D Vector representing the shots facing direction.
        """
        self.position = position
        self.direction = direction

class GameState:
    def __init__(self, tank, other_tanks=None, shots=None):
        """
        Holds the current state of the game, providing necessary information for decision-making.

        :param tank: TankObject representing the player's own tank.
        :param other_tanks: List of TankObject representing other tanks in the game.
        :param shots: List of ShotObject representing shots currently active in the game. Beware of incoming grenades!
        """
        self.tank = tank
        self.other_tanks = other_tanks if other_tanks is not None else []
        self.shots = shots if shots is not None else []

class OperatorActions:
    def __init__(self, turn = 0.0, turn_turret = 0.0, engine = 0.0, shoot = False):
        """
        Encapsulates the actions that a tank operator can take in a given frame.
        """
        self.turn = turn    # [-1.0 to 1.0] left to right respectively.
        self.turn_turret = turn_turret    # [-1.0 to 1.0] left to right respectively.
        self.engine = engine  # [-1.0 to 1.0] reverse to full ahead.
        self.shoot = shoot  # Set to True to fire cannon! Beware that cannon has to reload between shots.

class TankOperator:
    def get_tank_action(self,game_state):
        """
        This method should be implemented by the user to define the tank's actions based on the game state.

        :param game_state: GameState instance containing information about the current state of the game.
        :return: OperatorActions instance representing the tank's actions for the current frame.
        """
        raise NotImplementedError("This method should be overridden in a subclass")

    def get_operator_name(self):
        """
        Returns the name of the operator.

        :return: String representing the operator's name.
        """
        raise NotImplementedError("This method should be overridden in a subclass")

