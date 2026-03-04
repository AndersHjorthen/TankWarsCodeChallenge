import socket
import select
import time
import errno
import game_config as cfg

class TcpClient:
    def __init__(self, serverIp, serverPort):
        self.serverIp = serverIp
        self.serverPort = serverPort
        self.socket = None
        self.inited = False
        self.connect_in_progress = False
        self.connect_start_time = None
        self.connected = False
        self.debug = False

    def is_connected(self):
        return self.connected

    def run_client(self, bytes_to_send):
        timeout = cfg.CONNECTION_TIMEOUT_SECS  # Timeout in seconds for the connection attempt

        try:
            if not self.inited:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setblocking(False)
                self.inited = True
                if self.debug: print("Client initialised")

            elif not self.connect_in_progress and not self.connected:
                try:
                    self.connect_in_progress = True
                    self.connect_start_time = time.time()
                    self.socket.connect((self.serverIp, self.serverPort))
                    if self.debug: print("Client connection to server in progress")
                except socket.error as e:
                    time.sleep(1) # F#cking windows network stack is exhausted if I call connect too frequently!
                    if e.errno not in (errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN):
                        raise e
            if self.connect_in_progress:
                # Check if connection attempt is within the timeout period
                if time.time() - self.connect_start_time > timeout:
                    self.connect_in_progress = False
                    self.connect_start_time = None

                # Use select to check if the socket is writable
                _, writable, _ = select.select([], [self.socket], [], 0)

                if self.socket in writable:
                    # The socket is writable, indicating the connection attempt has completed
                    error_code = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                    if error_code != 0:
                        # A non-zero error code means the connection failed
                        raise socket.error(error_code)
                    # Connection was successful
                    self.connected = True
                    self.connect_in_progress = False
                    self.connect_start_time = None
                    if self.debug: print("Connection successful")

            if self.connected:
                if bytes_to_send:
                    self.socket.sendall(bytes_to_send)
                    if self.debug: print("Client sent bytes")

                bytesrecv = None

                try:
                    bytesrecv = self.socket.recv(cfg.SOCKET_BUFFER_SIZE)
                except socket.error as e:
                    if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                        raise e

                if b'' == bytesrecv:
                    # server hanging up
                    raise Exception("Server hung up resetting")

                if bytesrecv:
                    if self.debug: print("Client received bytes")

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
        if self.socket:
            self.socket.close()
            self.socket = None
