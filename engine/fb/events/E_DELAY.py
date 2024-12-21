import asyncio
import logging

from engine.desc import FbDesc, OutputDesc, ExecContext, InputDesc
from utils import parse_duration

logger = logging.getLogger(__name__)

class E_DELAY(FbDesc):
    def __init__(self):
        super().__init__(
            name='E_DELAY',
            inputs=[
                InputDesc(name='START', input_kind='event'),
                InputDesc(name='STOP', input_kind='event'),
                InputDesc(name='DT', input_kind='value'),
            ],
            outputs=[
                OutputDesc(name='EO', output_kind='event'),
            ],
        )

    async def exec(self, context: ExecContext, args: dict[str, any]):
        if context.io_name == 'START':
            if 'current_task' in context.store: return
            delay = parse_duration(args['DT'])

            task = asyncio.create_task(asyncio.sleep(delay))
            context.store['current_task'] = task
            logger.debug('Sleeping for %s seconds', delay)

            try:
                await task
                context.trigger('EO')
            except asyncio.CancelledError:
                logger.debug('Task cancelled')
                return

        if context.io_name == 'STOP':
            if 'current_task' not in context.store: return
            context.store['current_task'].cancel()
