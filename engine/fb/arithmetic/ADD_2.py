from engine.desc import FbDesc, InputDesc, OutputDesc, ExecContext


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
        res = sum([
            float(args['IN1']),
            float(args['IN2']),
        ])

        await context.supply_output('OUT', res)
        context.trigger('CNF')
