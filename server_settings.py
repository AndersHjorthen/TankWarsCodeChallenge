from keyboard_operator import KeyboardOperator
from dummy_operator import DummyOperator
from my_tank_operator import MyTankOperator
from operator_tcp_adapter import OperatorTCPadaptor_Server
from src.vec import Vec
import pygame
import game_config as cfg

starting_positions = cfg.STARTING_POSITION_NAMES

server_ip = cfg.DEFAULT_SERVER_IP  #TODO change on LAN!

def get_tank_operators_and_starting_positions():
    """ Edit to specify types of operators in game MIN two and MAX four players. """
    return {
        "red"   : DummyOperator(),
        "blue"  : KeyboardOperator("BlueBob"), #Default arrow keys
        "yellow": OperatorTCPadaptor_Server(server_ip),
        "green" : MyTankOperator(),
    }

server_fullscreen = False
