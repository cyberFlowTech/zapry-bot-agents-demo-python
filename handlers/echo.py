"""
Echo Handlers — demonstrates the manual registration pattern.

This module shows how to organise handlers in a separate file and
register them via a ``register(bot)`` function.  Compare this with
the decorator pattern used in ``bot.py`` for /start and /help.
"""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, filters

from services.echo_service import echo_service

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Command: /echo <text>
# ------------------------------------------------------------------

async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo back whatever the user typed after /echo."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "Usage: /echo <your message>\n\nExample: `/echo Hello World!`",
            parse_mode="Markdown",
        )
        return

    user_name = update.effective_user.username or update.effective_user.first_name
    reply = echo_service.format_echo(text, user_name)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔁 Echo Again", callback_data="echo_again"),
            InlineKeyboardButton("📊 Stats", callback_data="echo_stats"),
        ]
    ])

    await update.message.reply_text(reply, reply_markup=keyboard)
    logger.info("Echoed message for user %s", user_name)


# ------------------------------------------------------------------
# Callback: echo_again  /  echo_stats
# ------------------------------------------------------------------

async def echo_again_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Echo Again' inline button."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Send me any text and I'll echo it back! Or use /echo <text>."
    )


async def echo_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Stats' inline button — shows usage statistics."""
    query = update.callback_query
    await query.answer()

    stats = echo_service.get_stats()
    text = (
        "📊 *Echo Bot Stats*\n\n"
        f"• Messages echoed: {stats['echo_count']}\n"
        f"• Uptime: {stats['uptime_seconds']}s"
    )
    await query.message.reply_text(text, parse_mode="Markdown")


# ------------------------------------------------------------------
# Message: free-text in private chat
# ------------------------------------------------------------------

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo any non-command text message in private chats."""
    text = update.message.text or ""
    if not text:
        return

    user_name = update.effective_user.username or update.effective_user.first_name
    reply = echo_service.format_echo(text, user_name)
    await update.message.reply_text(reply)


# ------------------------------------------------------------------
# Registration function — called from bot.py
# ------------------------------------------------------------------

def register(bot) -> None:
    """Register all echo-related handlers with the bot.

    This is the *manual registration* pattern recommended for
    multi-file projects.  Each handler module exposes a ``register()``
    function that the main entry point calls after creating the bot.
    """
    # Command handler
    bot.add_command("echo", echo_command)

    # Callback query handlers
    bot.add_callback_query(r"^echo_again$", echo_again_callback)
    bot.add_callback_query(r"^echo_stats$", echo_stats_callback)

    # Free-text message handler (private chats only, non-commands)
    bot.add_message(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
        echo_message,
        group=10,
    )

    logger.info("Echo handlers registered")
