import logging

from engine.desc import FbDesc, OutputDesc, ExecContext, InputDesc

logger = logging.getLogger(__name__)

class STRING2STRING(FbDesc):
    def __init__(self):
        super().__init__(
            name='STRING2STRING',
            inputs=[
                InputDesc('REQ', 'event'),
                InputDesc('IN', 'value'),
            ],
            outputs=[
                OutputDesc('CNF', 'event'),
                OutputDesc('OUT', 'value')
            ],
        )

    async def exec(self, context: ExecContext, args: dict[str, any]):
        res = str(args['IN'])
        logger.debug('Converted %s -> %s', args['IN'], res)
        await context.supply_output('OUT', res)
        context.trigger('CNF')
