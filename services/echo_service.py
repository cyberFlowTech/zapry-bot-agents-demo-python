"""
Echo Service — simple business-logic layer.

Demonstrates the recommended pattern of separating business logic
from handler functions, making the code easier to test and reuse.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class EchoService:
    """Stateful service that formats echo responses and tracks usage."""

    _call_count: int = field(default=0, init=False, repr=False)
    _start_time: float = field(default_factory=time.time, init=False, repr=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def format_echo(self, text: str, user_name: str | None = None) -> str:
        """Return a formatted echo message and increment call counter."""
        self._call_count += 1
        greeting = f"@{user_name}" if user_name else "You"
        return f"🔁 {greeting} said:\n\n{text}"

    def get_about_text(self) -> str:
        """Return a short *About* blurb for the bot."""
        return (
            "🤖 *Echo Bot Demo*\n\n"
            "A minimal reference bot built with "
            "[zapry-bot-sdk-python](https://github.com/cyberFlowTech/zapry-bot-sdk-python).\n\n"
            "It demonstrates:\n"
            "• Command handlers (`/start`, `/echo`, `/help`)\n"
            "• Inline keyboard & callback queries\n"
            "• Free-text message handling\n"
            "• Service layer pattern\n"
            "• Lifecycle hooks & error handling"
        )

    def get_stats(self) -> dict:
        """Return simple usage statistics."""
        uptime = int(time.time() - self._start_time)
        return {
            "echo_count": self._call_count,
            "uptime_seconds": uptime,
        }


# Singleton instance — import this in handlers.
echo_service = EchoService()
