import logging
from typing import List

import bs4
from bs4 import BeautifulSoup

from .response import ResponseMessage, Response
from .models import model_index, ProtoEntity


logger = logging.getLogger(__name__)


class Request:
    id: int
    action: str
    resource_name: str
    payload: List[ProtoEntity]

    def __init__(self, request_id: int, action: str, resource_name: str, payload: List[ProtoEntity]):
        self.id = request_id
        self.action = action
        self.resource_name = resource_name
        self.payload = payload

    def to_response_message(self, reason = None, custom_payload: List[bs4.Tag] | None = None) -> ResponseMessage:
        return ResponseMessage.from_response(Response(self.id, reason, custom_payload))


class RequestMessage:
    resource_name: str
    xml_payload: str

    def __init__(self, resource_name, xml_payload):
        self.resource_name = resource_name
        self.xml_payload = xml_payload

    def parse_payload(self) -> Request:
        document = BeautifulSoup(self.xml_payload, 'xml')
        request = document.find(name='Request')

        request_id = request.attrs["ID"]
        request_action = request.attrs["Action"]
        payload = []

        for child in request.children:
            # noinspection PyUnresolvedReferences
            model_name = child.name
            if model_name not in model_index:
                logger.warning('Unknown model faced: %s', model_name)
                continue

            # noinspection PyTypeChecker
            payload.append(model_index[model_name](child))

        return Request(request_id, request_action, self.resource_name, payload)
