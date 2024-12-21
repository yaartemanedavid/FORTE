from engine.desc import FbDesc, InputDesc, OutputDesc, ExecContext


class OUT_ANY_CONSOLE(FbDesc):
    def __init__(self):
        super().__init__(
            name='OUT_ANY_CONSOLE',
            inputs=[
                InputDesc('REQ', 'event'),
                InputDesc('QI', 'value', True),
                InputDesc('LABEL', 'value', ''),
                InputDesc('IN', 'value', ''),
            ],
            outputs=[
                OutputDesc('CNF', 'event'),
                OutputDesc('QO', 'value'),
            ],
        )

    async def exec(self, context: ExecContext, args: dict[str, any]):
        print(f'label = {args['LABEL']}: {args['IN']}')
        context.trigger('CNF')
