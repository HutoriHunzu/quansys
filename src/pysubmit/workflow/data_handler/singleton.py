# singleton.py
from __future__ import annotations
from pathlib import Path
from threading import RLock


class PerPathSingleton(type):
    """
    Metaclass that returns one shared instance per (normalized) path.

    Any subclass **must** accept a `path` or `root` positional/keyword
    argument in its constructor.  The first time you call `Cls(path=...)`
    an instance is created and cached; subsequent calls with the same
    resolved path return the cached object.
    """

    _instances: dict[Path, object] = {}
    _lock: RLock = RLock()               # thread-safe

    def __call__(cls, *args, **kwargs):
        # Accept either 'path=' or 'root=' keyword, or the first arg
        if "path" in kwargs:
            raw = kwargs.pop("path")
        elif args:
            raw = args[0]
            args = args[1:]              # consume it
        else:
            raise TypeError("Path argument required")

        p = Path(raw)

        with cls._lock:
            if p in cls._instances:
                return cls._instances[p]
            instance = super().__call__(path=p, *args, **kwargs)
            cls._instances[p] = instance
            return instance