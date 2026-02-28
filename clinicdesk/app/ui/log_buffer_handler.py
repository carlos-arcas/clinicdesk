from __future__ import annotations

import logging
from collections import deque


class LogBufferHandler(logging.Handler):
    def __init__(self, capacity: int = 200) -> None:
        super().__init__()
        self._buffer: deque[str] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        self._buffer.append(self.format(record))

    def snapshot(self) -> list[str]:
        return list(self._buffer)
