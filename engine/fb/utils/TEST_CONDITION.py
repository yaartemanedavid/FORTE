import logging

from engine.desc import FbDesc, InputDesc, OutputDesc, ExecContext

logger = logging.getLogger(__name__)

class TEST_CONDITION(FbDesc):
    def __init__(self):
        super().__init__(
            name='TEST_CONDITION',
            inputs=[
                InputDesc('REQ', 'event'),
                InputDesc('check', 'value', False),
            ],
            outputs=[
                OutputDesc('CNF', 'event'),
            ],
        )

    async def exec(self, context: ExecContext, args: dict[str, any]):
        if args['check']:
            context.trigger('CNF')
