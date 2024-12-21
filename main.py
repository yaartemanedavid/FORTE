import asyncio
import logging
import sys
from os import getenv

from engine import EngineStore
from server import Listener


async def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(module)-10s | %(levelname)-5s | %(message)s', stream=sys.stdout)
    engines = EngineStore()

    try:
        Listener(
            getenv('BIND_ADDR'),
            int(getenv('BIND_PORT')),
            int(getenv('MAX_CONNS')),
            engines
        ).listen()
    except KeyboardInterrupt:
        logging.info('Shutdown requested')

if __name__ == '__main__':
    asyncio.run(main())
