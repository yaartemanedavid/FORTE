from socket import socket, AF_INET, SOCK_STREAM

from engine.core import Engine
from .client import Client


class Listener:
    bind_addr: str
    port: int
    max_conns: int
    engine: Engine

    def __init__(self, bind_addr: str, port: int, max_conns: int, engine: Engine):
        self.bind_addr = bind_addr
        self.port = port
        self.max_conns = max_conns
        self.engine = engine

    def listen(self):
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((self.bind_addr, self.port))
        s.listen(self.max_conns)

        print(f'server is listening on {self.bind_addr}:{self.port}')
        self.client_loop(s)

    def client_loop(self, s: socket):
        while True:
            conn, addr = s.accept()
            print(f'accepted connection from {addr}')
            c = Client(conn, addr, self.engine)
            c.start()
