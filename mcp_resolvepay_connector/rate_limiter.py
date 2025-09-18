#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "bibow"

import asyncio
import time
from typing import Optional


class RateLimiter:
    """Rate limiter for API calls to prevent exceeding limits"""

    def __init__(self, calls_per_second: int = 10):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second if calls_per_second > 0 else 0
        self.last_call_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def wait_if_needed(self) -> None:
        """Wait if needed to respect rate limits"""
        if self.calls_per_second <= 0:
            return

        async with self._lock:
            current_time = time.time()

            if self.last_call_time is not None:
                time_since_last_call = current_time - self.last_call_time
                if time_since_last_call < self.min_interval:
                    wait_time = self.min_interval - time_since_last_call
                    await asyncio.sleep(wait_time)
                    current_time = time.time()

            self.last_call_time = current_time

    def sync_wait_if_needed(self) -> None:
        """Synchronous version of wait_if_needed"""
        if self.calls_per_second <= 0:
            return

        current_time = time.time()

        if self.last_call_time is not None:
            time_since_last_call = current_time - self.last_call_time
            if time_since_last_call < self.min_interval:
                wait_time = self.min_interval - time_since_last_call
                time.sleep(wait_time)
                current_time = time.time()

        self.last_call_time = current_time

    def reset(self) -> None:
        """Reset the rate limiter state"""
        self.last_call_time = None