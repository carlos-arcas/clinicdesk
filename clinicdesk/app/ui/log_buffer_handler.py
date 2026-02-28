from __future__ import annotations

import logging
from collections import deque


class LogBufferHandler(logging.Handler):
    _shared: "LogBufferHandler | None" = None

    def __init__(self, capacity: int = 200) -> None:
        super().__init__()
        self._buffer: deque[tuple[str, str]] = deque(maxlen=capacity)
        LogBufferHandler._shared = self

    def emit(self, record: logging.LogRecord) -> None:
        run_id = str(getattr(record, "run_id", "-"))
        self._buffer.append((run_id, self.format(record)))

    def snapshot(self, run_id: str | None = None) -> list[str]:
        if not run_id:
            return [line for _, line in self._buffer]
        return [line for rec_run, line in self._buffer if rec_run == run_id]

    @classmethod
    def shared_snapshot(cls, run_id: str | None = None) -> list[str]:
        if cls._shared is None:
            return []
        return cls._shared.snapshot(run_id)
