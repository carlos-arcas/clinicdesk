from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class TemporalSplitNotEnoughDataError(ValueError):
    """No hay suficientes filas para generar split temporal válido."""


@dataclass(frozen=True, slots=True)
class TemporalSplitConfig:
    test_ratio: float = 0.2
    min_train: int = 20
    time_field: str = "inicio"


def temporal_train_test_split(rows: list[Any], cfg: TemporalSplitConfig) -> tuple[list[Any], list[Any]]:
    if not rows:
        raise TemporalSplitNotEnoughDataError("No se puede entrenar: no hay filas para split temporal.")
    ordered = sorted(rows, key=lambda row: _read_time_field(row, cfg.time_field))
    test_size = max(1, int(len(ordered) * cfg.test_ratio))
    train_rows = ordered[:-test_size]
    test_rows = ordered[-test_size:]
    if len(train_rows) < cfg.min_train:
        raise TemporalSplitNotEnoughDataError(
            f"Split temporal inválido: train={len(train_rows)} es menor que min_train={cfg.min_train}."
        )
    return train_rows, test_rows


def temporal_folds(rows: list[Any], n_folds: int = 3, min_train: int = 20) -> list[tuple[list[Any], list[Any]]]:
    if not rows:
        raise TemporalSplitNotEnoughDataError("No se puede crear folds sin datos.")
    ordered = sorted(rows, key=lambda row: _read_time_field(row, "inicio_ts"))
    size = len(ordered)
    fold_points = [(0.6, 0.2), (0.8, 0.2), (0.9, 0.1)][: max(0, n_folds)]
    folds: list[tuple[list[Any], list[Any]]] = []
    for train_ratio, test_ratio in fold_points:
        train_end = int(size * train_ratio)
        test_size = max(1, int(size * test_ratio))
        test_end = min(size, train_end + test_size)
        train_rows = ordered[:train_end]
        test_rows = ordered[train_end:test_end]
        if len(train_rows) < min_train or not test_rows:
            continue
        folds.append((train_rows, test_rows))
    if not folds:
        raise TemporalSplitNotEnoughDataError("No hay suficientes datos para folds temporales válidos.")
    return folds


def _read_time_field(row: Any, field_name: str) -> Any:
    if isinstance(row, dict):
        if field_name in row:
            return row[field_name]
        raise TemporalSplitNotEnoughDataError(f"Campo temporal '{field_name}' ausente en fila de split.")
    if hasattr(row, field_name):
        return getattr(row, field_name)
    raise TemporalSplitNotEnoughDataError(f"Campo temporal '{field_name}' ausente en fila de split.")
