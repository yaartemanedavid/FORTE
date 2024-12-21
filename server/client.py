import asyncio
import logging
from socket import socket
from threading import Thread
from typing import List

import bs4

from engine import fb_index, EngineStore, NoSuchResourceException, AlreadyExistsException
from engine.core import ResourceException
from engine.desc import parse_ref
from engine.fb import UnsupportedBlockException
from .proto import RequestMessage, ResponseMessage, Request, ProtoEntity, FB, Connection


logger = logging.getLogger(__name__)
MESSAGE_ENCODING = 'utf-8'


class ClientDisconnected(Exception):
    remote_addr: str

    def __init__(self, remote_addr):
        self.remote_addr = remote_addr


class Client(Thread):
    remote_addr: str
    s: socket
    engines: EngineStore

    def __init__(self, s: socket, remote_addr: str, engines: EngineStore):
        super().__init__()
        self.s = s
        self.remote_addr = remote_addr
        self.engines = engines

    def run(self):
        while True:
            try:
                msg = self.read_request_message()
                logger.debug('Received message for resource "%s": %s', msg.resource_name, msg.xml_payload)
                # print(msg.resource_name, msg.xml_payload)
                request = msg.parse_payload()
                if not self.process_request(request):
                    self.send_response_message(request.to_response_message())
            except ClientDisconnected as e:
                logger.info(f'Client {e.remote_addr} has disconnected')
                return
            except ResourceException as e:
                logger.error(e.message())

                if 'request' in locals():
                    # noinspection PyUnboundLocalVariable
                    self.send_response_message(request.to_response_message(reason=e.reason()))
            except NoSuchResourceException as e:
                logger.error('Client requested unknown resource %s', e.resource_name)

                if 'request' in locals():
                    # noinspection PyUnboundLocalVariable
                    self.send_response_message(request.to_response_message(reason='UNKNOWN_RESOURCE'))
            except AlreadyExistsException as e:
                logger.error('Client attempted to overwrite existing resource %s', e.resource_name)

                if 'request' in locals():
                    # noinspection PyUnboundLocalVariable
                    self.send_response_message(request.to_response_message(reason='ALREADY_EXISTS'))
            except UnsupportedBlockException as e:
                logger.error('Client requested unsupported block type %s', e.block_name)

                if 'request' in locals():
                    # noinspection PyUnboundLocalVariable
                    self.send_response_message(request.to_response_message(reason='UNSUPPORTED_BLOCK'))
            except Exception as e:
                logger.exception(f'Error handling client connection')
                if 'request' in locals():
                    # noinspection PyUnboundLocalVariable
                    self.send_response_message(request.to_response_message(reason='INTERNAL_ERROR'))
                raise e

    def process_request(self, request: Request) -> bool:
        if request.action == 'CREATE':
            self.process_create(request.resource_name, request.payload)
            return False
        elif request.action == 'WRITE':
            self.process_write(request.resource_name, request.payload)
            return False
        elif request.action == 'START':
            self.process_start(request)
            return True
        elif request.action == 'QUERY':
            self.process_query(request)
            return True
        elif request.action == 'DELETE':
            self.process_delete(request.payload)
            return False
        else:
            logger.error('Unknown action %s', request.action)
            return False

    def process_create(self, resource_name: str, entities: List[ProtoEntity]):
        if resource_name == '':
            self.process_create_resource(entities)
            return

        engine = self.engines.get_engine(resource_name)

        for entity in entities:
            if isinstance(entity, FB):
                fb_desc = fb_index.resolve(entity.type)
                engine.add_fb(entity.name, fb_desc)
            elif isinstance(entity, Connection):
                engine.add_connection(parse_ref(entity.source), parse_ref(entity.destination))
            else:
                logger.error('Unsupported entity type for CREATE', type(entity).__name__)

    def process_create_resource(self, entities: List[ProtoEntity]):
        for entity in entities:
            if isinstance(entity, FB) and entity.type == 'EMB_RES':
                self.engines.create_engine(entity.name)
            else:
                logger.error('Unsupported type for resource creation %s', type(entity).__name__)

    def process_write(self, resource_name: str, entities: List[ProtoEntity]):
        engine = self.engines.get_engine(resource_name)

        for entity in entities:
            if isinstance(entity, Connection):
                engine.add_input(parse_ref(entity.destination), entity.source)
            else:
                logger.error('Unsupported entity type for WRITE', type(entity).__name__)

    def process_start(self, request: Request):
        if request.resource_name not in self.engines.get_engines():
            raise NoSuchResourceException(request.resource_name)

        self.send_response_message(request.to_response_message())
        self.engines.get_engine(request.resource_name).start()
        logger.debug('Run finished')

    def process_query(self, request: Request):
        list_tag = bs4.Tag(name='FBList')

        for name in self.engines.get_engines().keys():
            current_tag = bs4.Tag(name='FB', attrs={'name': name, 'type': 'EMB_RES'})
            list_tag.append(current_tag)

        self.send_response_message(request.to_response_message(custom_payload=[list_tag]))

    def process_delete(self, entities: List[ProtoEntity]):
        for entity in entities:
            if isinstance(entity, FB):
                self.engines.delete_engine(entity.name)
            else:
                logger.error('Unsupported type for resource deletion %s', type(entity).__name__)

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
        logger.debug('Sent message %s', str(encoded_msg))

    def align(self):
        while self.read_word(1) != b'\x50': pass

    def read_word(self, length: int) -> bytes:
        buf = b''

        while len(buf) < length:
            chunk = self.s.recv(length - len(buf))
            if not chunk: raise ClientDisconnected(self.remote_addr)
            buf += chunk

        return buf
