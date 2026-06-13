"""Small helper for spacing infrared sends."""

from __future__ import annotations


class SendRateLimiter:
    """Track the minimum interval between infrared transmissions."""

    def __init__(self, minimum_interval: float) -> None:
        """Initialize the limiter."""
        self.minimum_interval = minimum_interval
        self._last_send_time: float | None = None

    def delay_until_next_send(self, now: float) -> float:
        """Return seconds to wait before sending again."""
        if self._last_send_time is None:
            return 0
        next_send_time = self._last_send_time + self.minimum_interval
        return max(0, next_send_time - now)

    def mark_sent(self, now: float) -> None:
        """Record a completed send time."""
        self._last_send_time = now

