import logging

from engine.desc import FbDesc, ExecContext

logger = logging.getLogger(__name__)

class EMB_RES(FbDesc):
    def __init__(self):
        super().__init__(
            name='EMB_RES',
            inputs=[],
            outputs=[],
        )

    async def exec(self, context: ExecContext, args: dict[str, any]):
        pass
