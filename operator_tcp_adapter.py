import traceback
import socket
import time
import json
import logging
from src.json_protocol import JSONProtocol
from src.vec import Vec
from tank_operator import TankOperator
from tank_operator import OperatorActions
from tank_operator import GameState
from tank_operator import TankObject
from tank_operator import ShotObject

logger = logging.getLogger(__name__)

from src.tcp_server import TcpServer
from src.tcp_client import TcpClient

class NameResponse:
    def __init__(self, name):
        self.name = name

class GameOverMessage:
    def __init__(self, game_over_message):
        self.game_over_message = game_over_message

class OperatorTCPadaptor_Server(TankOperator):
    def __init__(self, serverIp):
        self.tcp_server = TcpServer(serverIp)
        self.name = None
        self.json_protocol = JSONProtocol()
        self.latestOperatorAction = OperatorActions()

    def is_client_connected(self):
        return self.tcp_server.connected
    
    def get_connection_info_string(self):
        return self.tcp_server.serverIp + ":" + str(self.tcp_server.serverPort)

    def _run_server(self, object_to_send = None):
        try:
            bytes_to_send = None
            if object_to_send:
                bytes_to_send = self.json_protocol.encode(object_to_send)
            received_bytes = self.tcp_server.run_server(bytes_to_send)
            if received_bytes:
                jsonresponses = self.json_protocol.decode(received_bytes)
                for jsonresponse in jsonresponses:
                    if "name" in jsonresponse:
                        nr = NameResponse(**jsonresponse)
                        self.name = nr.name
                    elif "turn" in jsonresponse:
                        # Just overwrite older action response
                        self.latestOperatorAction =  OperatorActions(**jsonresponse)
        except Exception as e:
            logger.error("Server communication error: %s", e)
            self.json_protocol = JSONProtocol()
  
            
    def get_tank_action(self, game_state):
        self._run_server(game_state)
        return self.latestOperatorAction #always repeat latest action if nothing new

    def get_operator_name(self):       
        # designed for polling
        self._run_server()
        return self.name
    
    def send_game_over_message(self, message):
        self._run_server(GameOverMessage(message))             

class OperatorTCPadaptor_Client:
    def __init__(self, serverIp, serverPort, tankoperator):
        self.tankoperator = tankoperator
        self.json_protocol = JSONProtocol()
        self.tcp_client = TcpClient(serverIp, serverPort)
        self.bytes_to_send = None
        self.name_sent = False

        self._messages_received = 0
        self._actions_sent = 0
        self.game_over_message = None
    
    def deserialize_game_state(self,data):
        required_keys = ('tank', 'other_tanks', 'shots')
        for key in required_keys:
            if key not in data:
                raise KeyError("Missing required key in game state: '%s'" % key)

        def dict_to_vec(d):
            for k in ('x', 'y'):
                if k not in d:
                    raise KeyError("Missing required key in vec: '%s'" % k)
            return Vec(d['x'], d['y'])

        def dict_to_tank(d):
            for k in ('position', 'direction', 'turret_direction'):
                if k not in d:
                    raise KeyError("Missing required key in tank: '%s'" % k)
            return TankObject(dict_to_vec(d['position']), dict_to_vec(d['direction']), dict_to_vec(d['turret_direction']))

        def dict_to_shot(d):
            for k in ('position', 'direction'):
                if k not in d:
                    raise KeyError("Missing required key in shot: '%s'" % k)
            return ShotObject(dict_to_vec(d['position']), dict_to_vec(d['direction']))

        tank = dict_to_tank(data['tank'])
        other_tanks = [dict_to_tank(t) for t in data['other_tanks']]
        shots = [dict_to_shot(s) for s in data['shots']]

        return GameState(tank, other_tanks, shots)
    
    def run_client(self):
        try:
            received_bytes = self.tcp_client.run_client(self.bytes_to_send)
            self.bytes_to_send = None
            if received_bytes:
                jsonresponses = self.json_protocol.decode(received_bytes)
                if jsonresponses:
                    self._messages_received += len(jsonresponses)
                    lastmessage_json = jsonresponses[-1] # JUST USE LAST GAMESTATE others are stale..
                    try:
                        gamestate = self.deserialize_game_state(lastmessage_json)
                        try:
                            action = self.tankoperator.get_tank_action(gamestate)
                            self.bytes_to_send = self.json_protocol.encode(action)
                            self._actions_sent += 1
                        except Exception:
                            print(traceback.format_exc())
                    except (KeyError, TypeError) as e:
                        logger.error("Failed to deserialize game state: %s", e)
                        try:
                            self.game_over_message = GameOverMessage(**lastmessage_json).game_over_message
                        except (KeyError, TypeError) as e:
                            logger.error("Message from server not understood: %s - %s", lastmessage_json, e)

        except Exception as e:
            logger.error("Client communication error: %s", e)
            self.json_protocol = JSONProtocol()
            self.bytes_to_send = None
        
        if self.bytes_to_send == None and self.tcp_client.connected and not self.name_sent:
            self.bytes_to_send = self.json_protocol.encode(NameResponse(self.tankoperator.get_operator_name()))
            self.name_sent = True
        return None != self.bytes_to_send #True if more work, call again asap.