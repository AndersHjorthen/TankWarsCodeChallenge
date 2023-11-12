import pygame
from tank_operator import OperatorActions
from tank_operator import TankOperator

class DummyOperator(TankOperator):
    def get_actions(self):
        actions = OperatorActions(0,0,False)
        actions.turn = -1.0
        actions.shoot = True
        return actions
    
    def get_operator_name(self):
        return "Dummy"