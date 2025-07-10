"""
ledger.py
=========
JSON-backed run ledger that is **safe for multiprocessing** and keeps
its in-memory footprint small by loading the file fresh for every write
operation (“lazy reload on write”).

Concurrency model
-----------------
• A single `multiprocessing.Lock` is created by the parent script and
  passed to every worker via the pool’s *initializer*.
• All mutating methods (`allocate`, `attach_file`, `log_end`, `save`)
  acquire this lock so only one process reads-modify-writes the JSON at
  a time.
• The ledger content is *not* cached between calls; each mutating method
  reloads the JSON, applies its change, and writes the file back.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
from multiprocessing import Lock
from pydantic import BaseModel, Field
from .singleton import PerPathSingleton
from .status import Status
from contextlib import contextmanager
from typing import Generator

# ------------------------------------------------------------------ #
# global multiprocessing lock (set once by the pool initializer)
# ------------------------------------------------------------------ #
LEDGER_LOCK: Lock | None = None


def _locked(fn):
    """Wrap *fn* with the global LEDGER_LOCK if running under a pool."""

    def wrapper(self, *args, **kwargs):
        if LEDGER_LOCK is None:  # serial mode
            return fn(self, *args, **kwargs)
        with LEDGER_LOCK:
            return fn(self, *args, **kwargs)

    return wrapper


# ------------------------------------------------------------------ #
# model for a single run
# ------------------------------------------------------------------ #
class RunRecord(BaseModel):
    status: str = "PENDING"
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    files: dict[str, str] = Field(default_factory=dict)


# ------------------------------------------------------------------ #
# ledger: one instance per file / per process
# ------------------------------------------------------------------ #
class Ledger(metaclass=PerPathSingleton):
    """
    Usage
    -----
    >>> led = Ledger(path="results/metadata.json")
    >>> base = led.allocate("calibration", prefix="", hint=None)
    """

    def __init__(self, path: str | Path):
        self.file: Path = Path(path).expanduser().resolve()
        self.file.parent.mkdir(parents=True, exist_ok=True)

    # --------------- public, lock-protected API ---------------- #

    @_locked
    def allocate(self, identifier: str, prefix: str | None, hint: str | None) -> str:
        """
        Reserve a unique *base_path* for *identifier* and set status RUNNING.
        """
        data = self.data

        id_runs = data.setdefault(identifier, {})
        stem = hint or identifier
        base0 = "/".join(filter(None, [prefix, stem]))
        base = base0
        i = 1
        while base in id_runs:
            base = f"{base0}_{i:03d}"
            i += 1

        id_runs[base] = RunRecord(status=Status.RUNNING).model_dump(mode="json")
        self._save(data)
        return base

    @contextmanager
    def edit_record(self, identifier, base) -> Generator[RunRecord, None, None]:
        data = self.data
        record = RunRecord(**data[identifier][base])
        yield record
        data[identifier][base] = record.model_dump(mode='json')
        self._save(data)

    @_locked
    def attach_file(self, identifier: str, base: str, path_dict: dict[str, str]) -> None:

        with self.edit_record(identifier, base) as record:
            record.files.update(path_dict)

    @_locked
    def log_start(self, identifier: str, base: str) -> None:
        """
        Mark the run as RUNNING and stamp the start time.
        """

        with self.edit_record(identifier, base) as record:
            record.status = Status.RUNNING
            record.start_time = datetime.now()

    @_locked
    def log_end(self, identifier: str, base: str, status: str = Status.DONE) -> None:

        with self.edit_record(identifier, base) as record:
            record.status = status
            record.end_time = datetime.now()

    # convenience wrapper
    # save = _locked(lambda self: self._save(self.data))

    @property
    def data(self):
        return self._load()

    # --------------- internal helpers -------------------------- #
    def _load(self) -> dict[str, dict[str, dict]]:
        """Read the ledger JSON; return an in-memory dict."""
        if self.file.exists():
            with self.file.open("r") as f:
                return json.load(f)
        return {}

    def _save(self, data: dict[str, dict[str, dict]]) -> None:
        """Write *runs* back to disk, pretty-printed."""
        # tmp = self.file.with_suffix(".tmp")
        # tmp = self.file.with_suffix(".tmp")
        self.file.write_text(json.dumps(data, indent=2))
        # tmp.replace(self.file)
