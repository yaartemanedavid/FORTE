from asyncio import Event
from typing import List


class Ref:
    fb_id: str
    io_name: str

    def __init__(self, fb_id, io_name):
        self.fb_id = fb_id
        self.io_name = io_name

    def __str__(self):
        return f'Ref({self.fb_id}.{self.io_name})'


def parse_ref(io_id: str):
    fb_id, io_name = io_id.rsplit('.', 1)
    return Ref(fb_id, io_name)


class Lifecycle:
    start: Event

    def __init__(self, start_event: Event):
        self.start = start_event


class Controller:
    context_lifecycle: Lifecycle

    def __init__(self, context_lifecycle: Lifecycle):
        self.context_lifecycle = context_lifecycle

    def trigger(self, via: Ref):
        raise NotImplementedError()

    def supply(self, via: Ref, value: any):
        raise NotImplementedError()


class ExecContext:
    fb_id: str
    controller: Controller
    lifecycle: Lifecycle

    def __init__(self, fb_id: str, controller: Controller, lifecycle: Lifecycle):
        self.fb_id = fb_id
        self.controller = controller
        self.lifecycle = lifecycle

    async def supply_output(self, name: str, value: any):
        await self.controller.supply(Ref(self.fb_id, name), value)

    def trigger(self, name: str):
        self.controller.trigger(Ref(self.fb_id, name))

class InputDesc:
    name: str
    kind: str
    default_value: any

    def __init__(self, name: str, input_kind: str, default_value: any = None):
        self.name = name
        self.kind = input_kind
        self.default_value = default_value


class OutputDesc:
    name: str
    kind: str

    def __init__(self, name: str, output_kind: str):
        self.name = name
        self.kind = output_kind


class FbDesc:
    name: str
    inputs: List[InputDesc]
    outputs: List[OutputDesc]

    def __init__(self, name: str, inputs: List[InputDesc], outputs: List[OutputDesc]):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs

    def get_value_inputs(self) -> List[InputDesc]:
        return list(filter(lambda i: i.kind == 'value', self.inputs))

    async def exec(self, context: ExecContext, args: dict[str, any]):
        raise NotImplementedError()
