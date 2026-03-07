# -*- coding: utf-8 -*-
import socket
import errno
import game_config as cfg

class TcpServer:
    def __init__(self, serverIp):
        self.serverIp = serverIp
        self.serverPort = 0
        self.client_socket = None
        self.socket = None

        self.inited = False
        self.connected = False
        self.debug = False

        self.run_server(None)


    def run_server(self, bytes_to_send):
        try:
            if not self.inited:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.bind((self.serverIp, self.serverPort))  # Bind to an available port
                self.serverPort = self.socket.getsockname()[1]
                self.socket.listen(1)
                self.socket.setblocking(False)  # Set socket to non-blocking mode
                self.inited = True
                if self.debug: print("Server initialised")

            if not self.connected:
                try:
                    #wait for client
                    self.client_socket, addr = self.socket.accept()
                    self.client_socket.setblocking(False)
                    self.connected = True
                    if self.debug: print("Server connected")
                except socket.error:
                    pass

            else:
                if bytes_to_send:
                    self.client_socket.sendall(bytes_to_send)
                    if self.debug: print("Server sent bytes")

                bytesrecv = None

                try:
                    bytesrecv = self.client_socket.recv(cfg.SOCKET_BUFFER_SIZE)
                except socket.error as e:
                    if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                        raise e

                if b'' == bytesrecv:
                    # client hanging up
                    raise Exception("Client hung up resetting")

                if bytesrecv:
                    if self.debug: print("Server received bytes")

                return bytesrecv

        except Exception as ee:
            if self.debug: print("Resetting connection: " + str(ee))
            self.connected = False
            self.inited = False
            self.close()
            raise Exception('connection reset occured')

    def __del__(self):
        self.close()

    def close(self):
        self.socket.close()
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
