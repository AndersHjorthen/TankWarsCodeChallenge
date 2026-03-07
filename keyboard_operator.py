from __future__ import annotations

import pygame
from tank_operator import OperatorActions
from tank_operator import GameState
from tank_operator import TankOperator

class KeyboardOperator(TankOperator):
    def __init__(self, name: str,
                 fwdKey: int = pygame.K_UP,
                 backKey: int = pygame.K_DOWN,
                 leftKey: int = pygame.K_LEFT,
                 rightKey: int = pygame.K_RIGHT,
                 shootKey: int = pygame.K_KP0,
                 turretLeftKey: int = pygame.K_KP1,
                 turretRightKey: int = pygame.K_KP2) -> None:
        self.forwardKey: int = fwdKey #pygame.K_w
        self.backKey: int = backKey #pygame.K_s
        self.leftKey: int = leftKey #pygame.K_a
        self.rightKey: int = rightKey #pygame.K_d
        self.shootKey: int = shootKey #pygame.K_SPACE
        self.turretLeftKey: int = turretLeftKey
        self.turretRightKey: int = turretRightKey
        self.name: str = name

    def get_operator_name(self) -> str:
        return self.name

    def get_tank_action(self, _: GameState) -> OperatorActions:
        actions = OperatorActions(0,0,False)

        # Get the current state of all keyboard buttons
        keys = pygame.key.get_pressed()

        actions.engine = 0.0
        # Check for 'w' and 's' for engine control
        if keys[self.forwardKey]:
            actions.engine = 1.0
        if keys[self.backKey]:
            actions.engine += -1.0

        actions.turn = 0.0
        # Check for 'a' and 'd' for turning
        if keys[self.leftKey]:
            actions.turn = -1.0
        if keys[self.rightKey]:
            actions.turn += 1.0

        if keys[self.turretLeftKey]:
            actions.turn_turret = -1.0
        if keys[self.turretRightKey]:
            actions.turn_turret += 1.0

        # Check if spacebar is pressed for shooting
        actions.shoot = keys[self.shootKey]

        return actions
