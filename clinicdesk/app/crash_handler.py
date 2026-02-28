from __future__ import annotations

import logging
import sys
import threading
from types import TracebackType
from typing import Callable

_FATAL_KEY = "is_fatal_crash"


def install_global_exception_hook(logger: logging.LoggerAdapter) -> None:
    def _handle_exception(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            if sys.__excepthook__:
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            "unhandled_exception",
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={_FATAL_KEY: True},
        )

    sys.excepthook = _handle_exception

    if hasattr(threading, "excepthook"):
        def _thread_hook(args: threading.ExceptHookArgs) -> None:
            _handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

        threading.excepthook = _thread_hook  # type: ignore[assignment]


def fatal_exception_handler(logger: logging.LoggerAdapter) -> Callable[[type[BaseException], BaseException, TracebackType | None], None]:
    def _handler(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None) -> None:
        logger.critical(
            "unhandled_exception",
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={_FATAL_KEY: True},
        )

    return _handler
