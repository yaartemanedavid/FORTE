import logging

from engine.desc import FbDesc, OutputDesc, ExecContext, InputDesc

logger = logging.getLogger(__name__)

class BOOL2BOOL(FbDesc):
    def __init__(self):
        super().__init__(
            name='BOOL2BOOL',
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
        res = bool(args['IN'])
        logger.debug('Converted %s -> %t', args['IN'], res)
        await context.supply_output('OUT', res)
        context.trigger('CNF')
