from engine.desc import FbDesc
from engine.fb.arithmetic import *
from engine.fb.comparison import *
from engine.fb.convert import *
from engine.fb.events import *
from engine.fb.resources import *
from engine.fb.selection import *
from engine.fb.utils import *

class UnsupportedBlockException(Exception):
    block_name: str

    def __init__(self, block_name: str):
        self.block_name = block_name


class Index:
    blocks: dict[str, FbDesc]

    def __init__(self):
        self.blocks = {}

        self.register(ADD_2())
        self.register(ADD_3())
        self.register(ADD_4())
        self.register(F_DIV())
        self.register(F_MUL())
        self.register(F_SUB())

        self.register(F_EQ())
        self.register(F_GE())
        self.register(F_GT())
        self.register(F_LE())
        self.register(F_LT())
        self.register(F_NE())

        self.register(E_CYCLE())
        self.register(E_DELAY())
        self.register(E_RESTART())

        self.register(BOOL2BOOL())
        self.register(INT2INT())
        self.register(STRING2STRING())

        self.register(F_MAX())
        self.register(F_MIN())

        self.register(EMB_RES())
        self.register(OUT_ANY_CONSOLE())
        self.register(TEST_CONDITION())

    def register(self, desc: FbDesc):
        self.blocks[desc.name] = desc

    def resolve(self, name: str) -> FbDesc:
        if name not in self.blocks:
            raise UnsupportedBlockException(name)
        return self.blocks[name]


fb_index = Index()
