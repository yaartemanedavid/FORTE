import asyncio
import logging
from asyncio import Lock, Condition, Event
from typing import List

from engine.desc import ExecContext, InputDesc, FbDesc, Controller, Lifecycle, Ref
from engine.fb.events.E_RESTART import E_RESTART

logger = logging.getLogger(__name__)

class Value:
    current: any
    available: bool
    lock: Lock
    cond: Condition

    def __init__(self, value: any = None, available: bool = False):
        self.current = value
        self.available = available
        self.lock = Lock()
        self.cond = Condition()

    async def supply(self, value: any):
        logger.debug('Waiting for supply lock')
        await self.lock.acquire()
        self.current = value
        self.available = True
        self.lock.release()

        logger.debug('Supplied value, waiting for cond lock')
        await self.cond.acquire()
        self.cond.notify_all()
        self.cond.release()

        logger.debug('Successfully supplied value %s', self.current)

    async def acquire(self) -> any:
        if self.available:
            logger.debug('Immediately returning available value %s', self.current)
            self.available = False
            return self.current

        logger.debug('Acquiring cond lock')
        await self.cond.acquire()

        logger.debug('Waiting for value to be supplied')
        await self.cond.wait()
        self.cond.release()

        logger.debug('Value acquired, waiting for value lock')
        await self.lock.acquire()
        value = self.current
        self.available = False
        self.lock.release()

        logger.debug('Got value %s', value)
        return value

    def release(self):
        if self.lock.locked():
            self.lock.release()


class ValueContainer:
    values: dict[str, Value]

    def __init__(self, values: dict[str, Value]):
        self.values = values

    async def __aenter__(self):
        return await self.acquire_all()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.release_all()

    async def acquire_all(self) -> dict[str, any]:
        res = {}

        for k, v in self.values.items():
            logger.debug('Now will wait for %s value', k)
            res[k] = await v.acquire()

        return res

    def release_all(self):
        for v in self.values.values():
            v.release()


class FB:
    fb_id: str
    desc: FbDesc
    controller: Controller

    def __init__(self, fb_id: str, desc: FbDesc, controller: Controller):
        self.fb_id = fb_id
        self.desc = desc
        # self.outputs = outputs
        self.controller = controller

    # def get_output(self, o_name: str) -> Output:
    #     for o in self.outputs:
    #         if o.desc.name == o_name:
    #             return o
    #     else:
    #         raise Exception(f"No output with name {o_name}")

    async def exec(self, args: dict[str, any]):
        ctx = ExecContext(
            fb_id=self.fb_id,
            controller=self.controller,
            lifecycle=self.controller.context_lifecycle,
        )

        await self.desc.exec(ctx, args)

    def __str__(self):
        return f'FB({self.fb_id})'


class Entrypoint(FB):
    lifecycle: Lifecycle

    def __init__(self, fb_id: str, desc: FbDesc, controller: Controller, lifecycle: Lifecycle):
        super().__init__(fb_id, desc, controller)
        self.lifecycle = lifecycle


class Input:
    desc: InputDesc
    fb: FB
    prev_out: Ref

    def __init__(self, desc, fb):
        self.desc = desc
        self.fb = fb


class Connection:
    conn_id: str
    src: Ref
    dst: Ref
    value: Value

    def __init__(self, conn_id: str, src: Ref, dst: Ref, value = Value()):
        self.conn_id = conn_id
        self.src = src
        self.dst = dst
        self.value = value

    def __str__(self):
        return f'Connection({self.conn_id}, {self.src}, {self.dst}, "{self.value}")'


class InputConnection(Connection):
    def __init__(self, conn_id: str, dst: Ref, value: any):
        super().__init__(conn_id, Ref(0, 'IN'), dst, Value(value=value, available=True))

    def __str__(self):
        return f'InputConnection({self.conn_id}, {self.dst}, {self.value})'


class Engine(Controller):
    event_loop: asyncio.AbstractEventLoop
    tasks = []

    fb_index: dict[str, FB]
    connections: dict[str, Connection]
    lifecycle: Lifecycle
    entry_points: List[FB]

    last_conn_id = 0

    def __init__(self, event_loop: asyncio.AbstractEventLoop):
        self.lifecycle = Lifecycle(start_event=Event())
        super().__init__(self.lifecycle)

        self.fb_index = {}
        self.connections = {}
        self.entry_points = []

        self.event_loop = event_loop

    async def run(self):
        for entry_point in self.entry_points:
            logger.debug('Running entry point %s', entry_point)
            self.run_fb(entry_point)

        if len(self.entry_points) == 0:
            logger.error('No entry points found')

        logger.debug('Triggering start lifecycle event')
        self.lifecycle.start.set()

        for task in self.tasks:
            await task

    def add_fb(self, fb_id: str, desc: FbDesc):
        if fb_id in self.fb_index:
            raise Exception(f"FB with ID {fb_id} already exists")

        fb = FB(fb_id, desc, self)

        if isinstance(desc, E_RESTART):
            logger.debug('Registering FB %s as entry point', fb_id)
            self.entry_points.append(fb)

        self.fb_index[fb_id] = fb
        logger.info('Loaded FB %s %s', fb_id, desc)

    def add_connection(self, src: Ref, dst: Ref):
        if src.fb_id not in self.fb_index:
            raise Exception(f"No FB with ID {src.fb_id} found")

        if dst.fb_id not in self.fb_index:
            raise Exception(f"No FB with ID {dst.fb_id} found")

        self.last_conn_id += 1
        conn_id = str(self.last_conn_id)

        if conn_id in self.connections:
            raise Exception(f"Connection with ID {conn_id} already exists")

        conn = Connection(conn_id, src, dst, Value())
        self.connections[conn_id] = conn
        logger.info('Loaded connection %s %s', conn_id, conn)

    def add_input(self, dst: Ref, value: any):
        if dst.fb_id not in self.fb_index:
            raise Exception(f"No FB with ID {dst.fb_id} found")

        self.last_conn_id += 1
        conn_id = str(self.last_conn_id)

        if conn_id in self.connections:
            raise Exception(f"Connection with ID {conn_id} already exists")

        conn = InputConnection(conn_id, dst, value)
        self.connections[conn_id] = conn
        logger.info('Loaded input connection %s %s', conn_id, conn)

    def resolve_fb(self, ref: Ref) -> FB:
        if ref.fb_id not in self.fb_index:
            raise Exception(f"No FB with ID {ref.fb_id} found")

        fb = self.fb_index[ref.fb_id]
        return fb

    def get_outputs(self, src: Ref) -> list[Connection]:
        res = []

        for conn in self.connections.values():
            if conn.src.fb_id == src.fb_id and conn.src.io_name == src.io_name:
                res.append(conn)

        return res

    def get_inputs(self, dst: Ref) -> list[Connection]:
        res = []

        for conn in self.connections.values():
            if conn.dst.fb_id == dst.fb_id and conn.dst.io_name == dst.io_name:
                res.append(conn)

        return res

    def build_args(self, fb: FB) -> ValueContainer:
        values = {}

        for fb_input in fb.desc.get_value_inputs():
            inputs = self.get_inputs(Ref(fb.fb_id, fb_input.name))
            input_count = len(inputs)

            if input_count > 1:
                raise Exception(f"There should be zero ore one input, got {input_count} for {fb_input.name} of {fb.fb_id}")

            if input_count == 0:
                values[fb_input.name] = Value(value=fb_input.default_value, available=True)
            else:
                conn = inputs[0]
                values[fb_input.name] = conn.value

        return ValueContainer(values)

    async def exec_fb(self, fb: FB):
        logger.debug(f'Trying to acquire inputs for FB {fb.fb_id}')
        async with self.build_args(fb) as args:
            logger.debug(f'Acquired inputs for FB {fb.fb_id}')
            await fb.exec(args)
            logger.debug(f'Finished execution of FB {fb.fb_id}')
        logger.debug(f'Released inputs for FB {fb.fb_id}')

    def run_fb(self, fb: FB):
        logger.debug(f'Running FB {fb.fb_id}')
        self.tasks.append(asyncio.create_task(self.exec_fb(fb)))

    def trigger(self, via: Ref):
        logger.debug('Processing trigger from %s.%s', via.fb_id, via.io_name)

        outputs = self.get_outputs(via)
        if len(outputs) == 0:
            logger.debug('No outputs found for trigger')

        for conn in outputs:
            target_fb = self.resolve_fb(conn.dst)
            logger.debug('Dispatching trigger %s.%s -> %s.%s', via.fb_id, via.io_name, conn.dst.fb_id, conn.dst.io_name)
            self.run_fb(target_fb)

    async def supply(self, via: Ref, value: any):
        for conn in self.get_outputs(via):
            logger.debug('Processing supply of %s from %s to %s', value, via, conn.dst)
            await conn.value.supply(value)
