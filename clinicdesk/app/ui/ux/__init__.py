from __future__ import annotations

from typing import Any


__all__ = ["set_busy", "toast_error", "toast_info", "toast_success"]


def toast_success(*args: Any, **kwargs: Any) -> None:
    from clinicdesk.app.ui.ux.window_feedback import toast_success as _toast_success

    _toast_success(*args, **kwargs)


def toast_info(*args: Any, **kwargs: Any) -> None:
    from clinicdesk.app.ui.ux.window_feedback import toast_info as _toast_info

    _toast_info(*args, **kwargs)


def toast_error(*args: Any, **kwargs: Any) -> None:
    from clinicdesk.app.ui.ux.window_feedback import toast_error as _toast_error

    _toast_error(*args, **kwargs)


def set_busy(*args: Any, **kwargs: Any) -> None:
    from clinicdesk.app.ui.ux.window_feedback import set_busy as _set_busy

    _set_busy(*args, **kwargs)
