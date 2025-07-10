from enum import StrEnum, auto

class Status(StrEnum):
    PENDING = auto()
    RUNNING = auto()
    DONE    = auto()
    ERROR   = auto()