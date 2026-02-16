#!/usr/bin/env python3
"""
Zapry Echo Bot — minimal reference agent.

This single-file entry point shows both the **decorator** pattern
(for /start and /help) and the **manual registration** pattern
(for the echo module).  It is designed as a starting point that
developers can clone, configure, and extend.

Usage:
    1. cp .env.example .env  (then fill in your bot token)
    2. pip install -r requirements.txt
    3. python bot.py
"""

from __future__ import annotations

import logging
import os
import sys

# ---------------------------------------------------------------------------
# SDK path resolution (development only — before SDK is published to PyPI)
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SDK_CANDIDATES = [
    os.path.normpath(os.path.join(_THIS_DIR, "..", "zapry-bot-sdk-python")),
    os.path.normpath(os.path.join(_THIS_DIR, "..", "..", "zapry-bot-sdk-python")),
]
for _sdk in _SDK_CANDIDATES:
    if os.path.isdir(_sdk) and _sdk not in sys.path:
        sys.path.insert(0, _sdk)
        break

from zapry_bot_sdk import BotConfig, ZapryBot  # noqa: E402
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update  # noqa: E402
from telegram.ext import Application, ContextTypes  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("echo_bot")

# ---------------------------------------------------------------------------
# Bot initialisation
# ---------------------------------------------------------------------------
config = BotConfig.from_env()
bot = ZapryBot(config)


# ===========================================================================
# Decorator-style handlers  (simple commands defined right in bot.py)
# ===========================================================================

@bot.command("start")
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with inline keyboard buttons."""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Echo Something", callback_data="echo_again"),
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="echo_stats"),
        ],
    ])
    await update.message.reply_text(
        "👋 *Welcome to Echo Bot!*\n\n"
        "I'm a demo agent built with `zapry-bot-sdk-python`.\n\n"
        "Try these commands:\n"
        "• /echo <text> — I'll echo it back\n"
        "• /help — Show help message\n\n"
        "Or just send me any text!",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


@bot.command("help")
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message listing available commands."""
    await update.message.reply_text(
        "📖 *Echo Bot Commands*\n\n"
        "• /start — Welcome message\n"
        "• /echo <text> — Echo your text back\n"
        "• /help — This help message\n\n"
        "You can also just send any text in a private chat "
        "and I'll echo it right back!",
        parse_mode="Markdown",
    )


@bot.callback_query(r"^about$")
async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'About' inline button."""
    from services.echo_service import echo_service

    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        echo_service.get_about_text(),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ===========================================================================
# Lifecycle hooks
# ===========================================================================

@bot.on_post_init
async def post_init(application: Application) -> None:
    """Called after the bot application is initialised."""
    logger.info(
        "Echo Bot started — platform=%s  mode=%s",
        config.platform,
        config.runtime_mode,
    )


@bot.on_post_shutdown
async def post_shutdown(application: Application) -> None:
    """Called before the bot application shuts down."""
    logger.info("Echo Bot shutting down — goodbye!")


# ===========================================================================
# Global error handler
# ===========================================================================

@bot.on_error
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and send a user-friendly message if possible."""
    logger.error("Unhandled exception: %s", context.error, exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Oops! Something went wrong. Please try again later."
        )


# ===========================================================================
# Manual handler registration  (from handler modules)
# ===========================================================================

def register_handlers() -> None:
    """Import and register handler modules."""
    from handlers.echo import register as register_echo
    register_echo(bot)


# ===========================================================================
# Entry point
# ===========================================================================

def main() -> None:
    """Build, register, and run the bot."""
    register_handlers()
    logger.info("All handlers registered — launching bot …")
    bot.run()


if __name__ == "__main__":
    main()
