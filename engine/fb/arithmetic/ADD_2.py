import logging

from engine.desc import FbDesc, InputDesc, OutputDesc, ExecContext


logger = logging.getLogger(__name__)


class ADD_2(FbDesc):
    def __init__(self):
        super().__init__(
            name='ADD_2',
            inputs=[
                InputDesc('REQ', 'event'),
                InputDesc('IN1', 'value'),
                InputDesc('IN2', 'value'),
            ],
            outputs=[
                OutputDesc('CNF', 'event'),
                OutputDesc('OUT', 'value'),
            ],
        )

    async def exec(self, context: ExecContext, args: dict[str, any]):
        args = [
            float(args['IN1']),
            float(args['IN2']),
        ]

        logger.debug('Evaluating expression %s', ' + '.join(map(str, args)))
        res = sum(args)
        logger.debug('Got result: %s', res)

        await context.supply_output('OUT', res)
        context.trigger('CNF')
