import logging

from engine.desc import FbDesc, OutputDesc, ExecContext

logger = logging.getLogger(__name__)

class E_RESTART(FbDesc):
    def __init__(self):
        super().__init__(
            name='E_RESTART',
            inputs=[],
            outputs=[
                OutputDesc(name='COLD', output_kind='event'),
                OutputDesc(name='WARM', output_kind='event'),
                OutputDesc(name='STOP', output_kind='event'),
            ],
        )

    async def exec(self, context: ExecContext, args: dict[str, any]):
        logger.debug('Waiting for start lifecycle event to be triggered')
        await context.lifecycle.start.wait()
        context.trigger('WARM')
