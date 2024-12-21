import logging
from socket import socket, AF_INET, SOCK_STREAM

from engine import EngineStore
from .client import Client

logger = logging.getLogger(__name__)

class Listener:
    bind_addr: str
    port: int
    max_conns: int
    engines: EngineStore

    def __init__(self, bind_addr: str, port: int, max_conns: int, engines: EngineStore):
        self.bind_addr = bind_addr
        self.port = port
        self.max_conns = max_conns
        self.engines = engines

    def listen(self):
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((self.bind_addr, self.port))
        s.listen(self.max_conns)

        logger.info(f'server is listening on {self.bind_addr}:{self.port}')
        self.client_loop(s)

    def client_loop(self, s: socket):
        while True:
            conn, addr = s.accept()
            logger.info(f'accepted connection from {addr}')
            c = Client(conn, addr, self.engines)
            c.start()
