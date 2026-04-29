"""Graceful shutdown signal handling for long-running cron jobs."""

from __future__ import annotations

import signal
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ShutdownEvent:
    """Tracks whether a shutdown signal has been received."""
    triggered: bool = False
    signal_num: Optional[int] = None
    callbacks: List[Callable[[], None]] = field(default_factory=list)

    def trigger(self, sig: int) -> None:
        self.triggered = True
        self.signal_num = sig
        logger.warning("Shutdown signal %d received.", sig)
        for cb in self.callbacks:
            try:
                cb()
            except Exception as exc:  # pragma: no cover
                logger.error("Shutdown callback raised: %s", exc)

    def register_callback(self, cb: Callable[[], None]) -> None:
        """Register a function to call when a shutdown signal arrives."""
        self.callbacks.append(cb)

    @property
    def should_stop(self) -> bool:
        return self.triggered


_global_event: Optional[ShutdownEvent] = None


def setup_signal_handlers(
    signals: tuple[int, ...] = (signal.SIGTERM, signal.SIGINT),
) -> ShutdownEvent:
    """Install signal handlers and return the shared ShutdownEvent."""
    global _global_event
    event = ShutdownEvent()
    _global_event = event

    def _handler(sig: int, _frame: object) -> None:
        event.trigger(sig)

    for sig in signals:
        signal.signal(sig, _handler)
        logger.debug("Registered handler for signal %d.", sig)

    return event


def get_event() -> Optional[ShutdownEvent]:
    """Return the currently active ShutdownEvent, if any."""
    return _global_event


def render_shutdown_report(event: ShutdownEvent) -> str:
    """Return a human-readable summary of the shutdown event."""
    if not event.triggered:
        return "No shutdown signal received."
    sig_name = signal.Signals(event.signal_num).name if event.signal_num else "UNKNOWN"
    return f"Shutdown triggered by signal {sig_name} ({event.signal_num})."
