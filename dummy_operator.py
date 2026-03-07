from tank_operator import OperatorActions
from tank_operator import TankOperator

class DummyOperator(TankOperator):
    def get_tank_action(self, _):
        actions = OperatorActions(0,0,False)
        actions.turn = -1.0
        actions.shoot = True
        return actions
    
    def get_operator_name(self):
        return "Dummy"