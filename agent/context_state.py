from enum import Enum, auto
class ContextState(Enum):
    EVENT = 0
    MAP = auto()
    COMBAT = auto()
    REWARD = auto()
    SHOP = auto()
    REST = auto()
    INVALID = auto()

