import logging

from engine.core import Engine

logger = logging.getLogger(__name__)

class NoSuchResourceException(Exception):
    resource_name: str

    def __init__(self, resource_name: str):
        self.resource_name = resource_name


class AlreadyExistsException(Exception):
    resource_name: str

    def __init__(self, resource_name: str):
        self.resource_name = resource_name


class EngineStore:
    engines: dict[str, Engine]

    def __init__(self):
        self.engines = {}

    def create_engine(self, resource_name: str):
        if resource_name in self.engines:
            raise AlreadyExistsException(resource_name)

        self.engines[resource_name] = Engine()
        logger.info(f'Created engine {resource_name}')

    def delete_engine(self, resource_name: str):
        if resource_name in self.engines:
            del self.engines[resource_name]
            logger.info(f'Deleted engine {resource_name}')
        else:
            raise NoSuchResourceException(resource_name)

    def get_engine(self, resource_name: str) -> Engine:
        if resource_name not in self.engines:
            raise NoSuchResourceException(resource_name)

        return self.engines[resource_name]

    def get_engines(self) -> dict[str, Engine]:
        return self.engines
