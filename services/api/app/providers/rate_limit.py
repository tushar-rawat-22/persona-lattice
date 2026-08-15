# SPDX-License-Identifier: Apache-2.0
from collections import deque
from collections.abc import Callable
import time

from .errors import ProviderRateBudgetExceeded


class RateBudget:
    def __init__(
        self,
        *,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit < 1 or window_seconds <= 0:
            raise ValueError("Rate budget requires a positive limit and window.")
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self._events: deque[float] = deque()

    def consume(self) -> None:
        now = self.clock()
        cutoff = now - self.window_seconds
        while self._events and self._events[0] <= cutoff:
            self._events.popleft()
        if len(self._events) >= self.limit:
            raise ProviderRateBudgetExceeded("Local provider rate budget is exhausted.")
        self._events.append(now)
