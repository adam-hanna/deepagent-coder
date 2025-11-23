"""Streaming output handler for real-time token display"""

import asyncio
from typing import Optional, Callable, List

class StreamingHandler:
    """
    Handles streaming output from LLM with real-time display

    Accumulates tokens and optionally calls a callback for each token.
    Supports rate limiting to prevent overwhelming the display.
    """

    def __init__(
        self,
        callback: Optional[Callable[[str], None]] = None,
        rate_limit: float = 0.0
    ):
        """
        Initialize streaming handler

        Args:
            callback: Optional function to call for each token
            rate_limit: Minimum seconds between token callbacks (0 = no limit)
        """
        self.callback = callback
        self.rate_limit = rate_limit
        self._accumulated: List[str] = []
        self._last_call_time: float = 0.0

    async def on_token(self, token: str) -> None:
        """
        Process a single token

        Args:
            token: Token string to process
        """
        # Add to accumulation
        self._accumulated.append(token)

        # Apply rate limiting if configured
        if self.rate_limit > 0:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - self._last_call_time
            if elapsed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - elapsed)
            self._last_call_time = asyncio.get_event_loop().time()

        # Call callback if provided
        if self.callback:
            self.callback(token)

    def get_accumulated(self) -> str:
        """
        Get accumulated tokens as single string

        Returns:
            Concatenated token string
        """
        return "".join(self._accumulated)

    def reset(self) -> None:
        """Reset handler state"""
        self._accumulated = []
        self._last_call_time = 0.0
