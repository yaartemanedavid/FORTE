import asyncio
import logging
from socket import socket
from threading import Thread
from typing import List

from engine import fb_index
from engine.core import Engine
from engine.desc import parse_ref
from .proto import RequestMessage, ResponseMessage, Request, ProtoEntity, FB, Connection

logger = logging.getLogger(__name__)


MESSAGE_ENCODING = 'utf-8'


class Client(Thread):
    remote_addr: str
    s: socket
    engine: Engine

    def __init__(self, s: socket, remote_addr: str, engine: Engine):
        super().__init__()
        self.s = s
        self.remote_addr = remote_addr
        self.engine = engine

    def run(self):
        while True:
            try:
                msg = self.read_request_message()
                # print(msg.resource_name, msg.xml_payload)
                request = msg.parse_payload()
                self.process_request(request)
                self.send_response_message(ResponseMessage('<Response ID="0"/>'))
            except:
                logger.exception('Error handling client connection')
                return

    def process_request(self, request: Request):
        if request.action == 'CREATE':
            self.process_create(request.payload)
        elif request.action == 'WRITE':
            self.process_write(request.payload)
        elif request.action == 'START':
            asyncio.run(self.engine.run())
            logger.debug('Run finished')
        else:
            logger.error('Unknown action %s', request.action)


    def process_create(self, entities: List[ProtoEntity]):
        for entity in entities:
            if isinstance(entity, FB):
                fb_desc = fb_index.resolve(entity.type)
                self.engine.add_fb(entity.name, fb_desc)
            elif isinstance(entity, Connection):
                self.engine.add_connection(parse_ref(entity.source), parse_ref(entity.destination))
            else:
                logger.error('Unsupported entity type for CREATE', type(entity).__name__)

    def process_write(self, entities: List[ProtoEntity]):
        for entity in entities:
            if isinstance(entity, Connection):
                self.engine.add_input(parse_ref(entity.destination), entity.source)
            else:
                logger.error('Unsupported entity type for WRITE', type(entity).__name__)

    def read_request_message(self) -> RequestMessage:
        self.align()
        resource_name_length = int.from_bytes(self.read_word(2), byteorder='big', signed=False)
        resource_name = self.read_word(resource_name_length).decode(MESSAGE_ENCODING)

        self.align()
        payload_length = int.from_bytes(self.read_word(2), byteorder='big', signed=False)
        payload = self.read_word(payload_length).decode(MESSAGE_ENCODING)

        return RequestMessage(resource_name, payload)

    def send_response_message(self, msg: ResponseMessage):
        self.s.send(b'\x50')
        encoded_msg = msg.xml_payload.encode(MESSAGE_ENCODING)
        self.s.send(len(encoded_msg).to_bytes(2, byteorder='big', signed=False))
        self.s.send(encoded_msg)

    def align(self):
        while self.read_word(1) != b'\x50': pass

    def read_word(self, length: int) -> bytes:
        buf = b''

        while len(buf) < length:
            chunk = self.s.recv(length - len(buf))
            if not chunk: raise RuntimeError(f'client {self.remote_addr} disconnected')
            buf += chunk

        return buf
