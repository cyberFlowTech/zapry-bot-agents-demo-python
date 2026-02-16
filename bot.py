#!/usr/bin/env python3
"""
Zapry Bot Agent Demo — 完整版 AI Agent 模板

基于 zapry-bot-sdk-python 构建的 AI Agent 开发参考实现，
展示 AI 对话、长期记忆、意图识别、塔罗占卜、群组互动、USDT 支付等完整能力。

Usage:
  1. cp .env.example .env (填入配置)
  2. pip install -r requirements.txt
  3. python bot.py
"""

from __future__ import annotations

import logging
import os
import sys

# ---------------------------------------------------------------------------
# SDK 路径解析（开发阶段，SDK 尚未发布到 PyPI）
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
from telegram import Update  # noqa: E402
from telegram.ext import Application, ContextTypes  # noqa: E402

from config import DEBUG, LOG_FILE  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.DEBUG if DEBUG else logging.INFO,
)
for _name in ("httpx", "httpcore"):
    logging.getLogger(_name).setLevel(logging.WARNING)

logger = logging.getLogger("agent_bot")

# ---------------------------------------------------------------------------
# Bot 初始化
# ---------------------------------------------------------------------------
config = BotConfig.from_env()
bot = ZapryBot(config)


# ===========================================================================
# 全局命令（装饰器模式）
# ===========================================================================

@bot.command("start")
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """欢迎消息"""
    user = update.effective_user.first_name or "朋友"
    text = (
        f"你好 {user}，我是晚晴 🌙\n\n"
        "很高兴认识你~\n\n"
        "我是一名塔罗牌解读师，平时帮大家看看牌面、聊聊困惑。\n\n"
        "你可以：\n"
        "• 直接和我聊天，说什么都可以\n"
        "• 发 /tarot 加上问题，我帮你占卜\n"
        "• 发 /help 看看我还能做什么\n\n"
        "塔罗揭示的是趋势，真正做决定的人，始终是你。\n\n"
        "有什么想聊的吗？我在这里听你说~\n\n"
        "— 晚晴 🌿"
    )
    try:
        await update.message.reply_text(text, reply_to_message_id=update.message.message_id)
    except Exception:
        await update.message.reply_text(text)


@bot.command("help")
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """帮助信息"""
    from config import FREE_TAROT_DAILY, FREE_CHAT_DAILY, PRICE_TAROT_DETAIL, PRICE_TAROT_READING, PRICE_AI_CHAT

    chat = update.effective_chat

    base_help = f"""嘿，我来介绍一下我能做的事~ 🌙
━━━━━━━━━━━━━━━━━

💬 和我聊天
━━━━━━━━━━━━━━━━━

直接发消息给我就好，什么都可以聊。
在群里 @我，我也会回复~

/intro - 想更了解我的话
/memory - 看看我记住了你什么
/clear - 清空我们的聊天记录
/forget - 让我忘掉关于你的一切

我会记住你告诉我的事，这样能给你更贴心的建议 💭

━━━━━━━━━━━━━━━━━
🎴 塔罗占卜
━━━━━━━━━━━━━━━━━

/tarot 你的问题 - 正式占卜（一张张翻牌）
/fortune 你的问题 - 快速求个指引
/luck - 看看今天的运势
/history - 翻翻以前的占卜记录

试试看：
• /tarot 我应该换工作吗
• /tarot 这段感情有结果吗

━━━━━━━━━━━━━━━━━
💎 关于充值
━━━━━━━━━━━━━━━━━

每天有免费额度：占卜 {FREE_TAROT_DAILY} 次，聊天 {FREE_CHAT_DAILY} 次。
运势、快速求问、历史记录这些都不限~

用完了也没关系，充一点 USDT 就能继续：
• 📖 深度解读 {PRICE_TAROT_DETAIL} USDT
• 🎴 超额占卜 {PRICE_TAROT_READING} USDT
• 💬 超额聊天 {PRICE_AI_CHAT} USDT

/recharge - 充值
/balance - 看看余额
"""

    group_help = """
━━━━━━━━━━━━━━━━━
👥 群里的玩法
━━━━━━━━━━━━━━━━━

/group_fortune - 今天群里的运势
/ranking - 看看谁运势最好
/pk - 和朋友来一场塔罗对决

在群里占卜会自动加入排行榜，
@我也可以直接聊天哦~
"""

    if chat.type in ['group', 'supergroup']:
        help_text = base_help + group_help
    else:
        help_text = base_help + "\n\n把我拉进群组，还有更多好玩的~ 👥"

    help_text += "\n━━━━━━━━━━━━━━━━━\n\n记住，我不替你做决定，只帮你看清选择。\n真正的力量，在你自己手中~\n\n— 晚晴 🌿"

    try:
        await update.message.reply_text(help_text, reply_to_message_id=update.message.message_id)
    except Exception:
        await update.message.reply_text(help_text)


# ===========================================================================
# 生命周期钩子
# ===========================================================================

@bot.on_post_init
async def post_init(application: Application) -> None:
    """应用初始化后：建表 + 启动链上监听"""
    from db.database import db
    db.init_tables()
    from services.chat_history import chat_history_manager
    chat_history_manager.ensure_table()
    logger.info("✅ 数据库初始化完成")

    from services.chain_monitor import chain_monitor
    chain_monitor.set_bot(application.bot)
    await chain_monitor.start()


@bot.on_post_shutdown
async def post_shutdown(application: Application) -> None:
    """应用关闭前：停止后台服务"""
    from services.chain_monitor import chain_monitor
    await chain_monitor.stop()


# ===========================================================================
# 全局错误处理
# ===========================================================================

@bot.on_error
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """记录错误并友好提示用户"""
    logger.error("Unhandled exception: %s", context.error, exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "啊，我刚才走神了一下 😅 能再说一遍吗？\n\n如果一直有问题，过一会儿再找我就好~"
            )
        except Exception:
            pass


# ===========================================================================
# Handler 注册
# ===========================================================================

def register_handlers() -> None:
    """注册所有 handler 模块"""
    from handlers.chat import register as reg_chat
    from handlers.tarot import register as reg_tarot
    from handlers.fortune import register as reg_fortune
    from handlers.luck import register as reg_luck
    from handlers.group import register as reg_group
    from handlers.payment import register as reg_payment

    reg_chat(bot)
    reg_tarot(bot)
    reg_fortune(bot)
    reg_luck(bot)
    reg_group(bot)
    reg_payment(bot)

    logger.info("✅ 所有 handler 已注册")


# ===========================================================================
# 入口
# ===========================================================================

def main() -> None:
    from config import get_current_config_summary
    logger.info(get_current_config_summary())
    register_handlers()
    logger.info("Bot 启动中...")
    bot.run()


if __name__ == "__main__":
    main()
