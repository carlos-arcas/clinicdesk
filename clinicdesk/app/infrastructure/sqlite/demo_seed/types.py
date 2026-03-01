from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class BatchProgress:
    phase: str
    total_items: int
    total_batches: int
    started_at: datetime

    def log_batch(self, batch_index: int, done: int) -> None:
        elapsed_s = max((datetime.now(UTC) - self.started_at).total_seconds(), 1e-6)
        rate = done / elapsed_s
        pending = max(0, self.total_items - done)
        eta_s = pending / rate if rate > 0 else 0.0
        LOGGER.info(
            "seed_progress",
            extra={
                "phase": self.phase,
                "batch_index": batch_index,
                "batch_total": self.total_batches,
                "done": done,
                "total": self.total_items,
                "elapsed_s": round(elapsed_s, 2),
                "rate": round(rate, 2),
                "eta_s": round(eta_s, 2),
            },
        )
