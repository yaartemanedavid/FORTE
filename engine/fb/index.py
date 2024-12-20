from engine.desc import FbDesc
from engine.fb.arithmetic import *
from engine.fb.convert import *
from engine.fb.events import *
from engine.fb.resources import *
from engine.fb.utils import *


class Index:
    blocks: dict[str, FbDesc]

    def __init__(self):
        self.blocks = {}

        self.register(ADD_2())
        self.register(ADD_3())
        self.register(ADD_4())

        self.register(E_RESTART())

        self.register(STRING2STRING())
        self.register(INT2INT())

        self.register(EMB_RES())
        self.register(OUT_ANY_CONSOLE())

    def register(self, desc: FbDesc):
        self.blocks[desc.name] = desc

    def resolve(self, name: str) -> FbDesc:
        return self.blocks[name]


fb_index = Index()
