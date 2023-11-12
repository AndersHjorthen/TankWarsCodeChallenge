from tank_operator import OperatorActions
from tank_operator import GameState
from tank_operator import TankOperator
from src.vec import Vec

class MyTankOperator(TankOperator):
    def __init__(self):
        self.name = "Insert Name here"
    
    def get_operator_name(self):
        return self.name
    
    def get_actions(self, gamestate):
        return OperatorActions()