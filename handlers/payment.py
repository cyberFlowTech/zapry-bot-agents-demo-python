"""
充值与余额命令处理器
/recharge - USDT 充值（展示用户专属热钱包地址）
/balance  - 查看余额和用量
/topup    - 管理员手动充值
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.payment import payment_manager
from services.quota import quota_manager
from services.wallet import wallet_manager
from config import (
    HD_MNEMONIC,
    PRICE_TAROT_DETAIL,
    PRICE_TAROT_READING,
    PRICE_AI_CHAT,
    FREE_TAROT_DAILY,
    FREE_CHAT_DAILY,
    ADMIN_USER_IDS,
)
import logging

logger = logging.getLogger(__name__)


# ========== 安全回复 ==========

async def _safe_reply(message, text: str, reply_markup=None):
    """安全引用回复，Zapry 不支持时自动降级"""
    try:
        return await message.reply_text(
            text,
            reply_to_message_id=message.message_id,
            reply_markup=reply_markup
        )
    except Exception:
        return await message.reply_text(text, reply_markup=reply_markup)


# ========== 充值地址展示（共用文案） ==========

def _build_recharge_text(deposit_address: str, balance: float) -> str:
    """构建充值说明文案（晚晴口吻）"""
    text = (
        f"这是你的专属充值地址~ 💎\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📍 充值地址（BSC 链 USDT）：\n"
        f"{deposit_address}\n\n"
        f"转多少都可以，到账后会自动帮你充上。\n"
        f"一般 1-3 分钟就好啦~\n\n"
        f"小提醒：\n"
        f"• 只支持 BSC 链上的 USDT 哦\n"
        f"• 这个地址是你专属的，可以反复用\n"
        f"• 别转其他币到这里，我认不出来的 😅\n\n"
    )

    if balance > 0:
        text += f"你现在的余额是 {balance:.4f} USDT\n\n"

    text += "到账了我会第一时间告诉你~ ✨\n\n— 晚晴 🌿"
    return text


# ========== /recharge 充值命令 ==========

async def recharge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """USDT 充值命令"""
    user_id = str(update.effective_user.id)

    if not HD_MNEMONIC:
        await _safe_reply(update.message, "充值还没有开放呢，我去催催管理员~ 😊")
        return

    try:
        wallet = await wallet_manager.get_or_create_wallet(user_id)
    except RuntimeError as e:
        logger.error(f"❌ 钱包创建失败: {e}")
        await _safe_reply(update.message, "抱歉，充值功能暂时有点问题，过一会儿再试试好吗？")
        return

    deposit_address = wallet["address"]
    await payment_manager.create_recharge_order(user_id, deposit_address)
    balance = await payment_manager.get_balance(user_id)

    text = _build_recharge_text(deposit_address, balance)
    keyboard = [[InlineKeyboardButton("💰 看看余额", callback_data='check_balance')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await _safe_reply(update.message, text, reply_markup=reply_markup)
    logger.info(f"💎 充值页面 | 用户: {user_id} | 地址: {deposit_address[:12]}...")


# ========== /balance 余额命令 ==========

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看余额和今日用量"""
    user_id = str(update.effective_user.id)

    import asyncio
    balance_info, daily_summary = await asyncio.gather(
        payment_manager.get_balance_info(user_id),
        quota_manager.get_daily_summary(user_id)
    )

    balance = balance_info["balance"]
    total_recharged = balance_info["total_recharged"]
    total_spent = balance_info["total_spent"]

    text = f"你的账户情况~ 💰\n━━━━━━━━━━━━━━━━━\n\n"
    text += f"💎 余额：{balance:.4f} USDT\n\n"

    if total_recharged > 0:
        text += (
            f"到目前为止，你一共充了 {total_recharged:.4f} USDT，\n"
            f"用掉了 {total_spent:.4f} USDT。\n\n"
        )

    # 今日用量
    tarot_left = daily_summary['tarot_free_remaining']
    chat_left = daily_summary['chat_free_remaining']

    text += "━━━━━━━━━━━━━━━━━\n"
    text += "📋 今天的免费额度\n━━━━━━━━━━━━━━━━━\n\n"

    if tarot_left > 0:
        text += f"🎴 占卜还剩 {tarot_left} 次免费\n"
    else:
        text += f"🎴 占卜免费次数已用完（{PRICE_TAROT_READING} USDT/次）\n"

    if chat_left > 0:
        text += f"💬 聊天还剩 {chat_left} 次免费\n\n"
    else:
        text += f"💬 聊天免费次数已用完（{PRICE_AI_CHAT} USDT/次）\n\n"

    text += (
        f"━━━━━━━━━━━━━━━━━\n"
        f"💎 价格一览\n━━━━━━━━━━━━━━━━━\n\n"
        f"📖 深度解读 {PRICE_TAROT_DETAIL} USDT/次\n"
        f"🎴 占卜每天 {FREE_TAROT_DAILY} 次免费，之后 {PRICE_TAROT_READING} USDT/次\n"
        f"💬 聊天每天 {FREE_CHAT_DAILY} 次免费，之后 {PRICE_AI_CHAT} USDT/次\n"
        f"✨ 运势、求问、历史记录都是免费的~\n\n"
        f"— 晚晴 🌿"
    )

    keyboard = [[InlineKeyboardButton("💎 去充值", callback_data='go_recharge')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await _safe_reply(update.message, text, reply_markup=reply_markup)


# ========== 回调处理 ==========

async def check_balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看余额的回调按钮"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    user_id = str(query.from_user.id)
    balance = await payment_manager.get_balance(user_id)

    if balance > 0:
        text = f"你现在有 {balance:.4f} USDT 💎\n\n想看详细的使用情况，发 /balance 给我就好~"
    else:
        text = "你的余额还是 0 呢~ 充一点就能解锁更多功能啦 💎"

    await context.bot.send_message(chat_id=query.message.chat.id, text=text)


async def go_recharge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """去充值的回调按钮 — 直接展示用户专属充值地址"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    user_id = str(query.from_user.id)
    chat_id = query.message.chat.id

    if not HD_MNEMONIC:
        await context.bot.send_message(chat_id=chat_id, text="充值还没有开放呢，我去催催管理员~ 😊")
        return

    try:
        wallet = await wallet_manager.get_or_create_wallet(user_id)
    except RuntimeError:
        await context.bot.send_message(chat_id=chat_id, text="抱歉，充值功能暂时有点问题，过一会儿再试试好吗？")
        return

    deposit_address = wallet["address"]
    balance = await payment_manager.get_balance(user_id)
    await payment_manager.create_recharge_order(user_id, deposit_address)

    text = _build_recharge_text(deposit_address, balance)
    keyboard = [[InlineKeyboardButton("💰 看看余额", callback_data='check_balance')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


# ========== 管理员命令 ==========

async def topup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员手动充值"""
    admin_id = str(update.effective_user.id)

    if admin_id not in ADMIN_USER_IDS:
        await _safe_reply(update.message, "这个命令只有管理员能用哦~")
        return

    if not context.args or len(context.args) < 2:
        await _safe_reply(
            update.message,
            "用法：/topup 用户ID 金额\n\n例如：/topup 548348 10"
        )
        return

    try:
        target_user_id = context.args[0]
        amount = float(context.args[1])
        if amount <= 0:
            await _safe_reply(update.message, "金额要大于 0 哦~")
            return
    except ValueError:
        await _safe_reply(update.message, "格式不对~ 用法：/topup 用户ID 金额")
        return

    new_balance = await payment_manager.add_balance(target_user_id, amount, tx_hash="manual_topup")

    text = (
        f"已为用户充值 ✅\n\n"
        f"用户：{target_user_id}\n"
        f"金额：{amount} USDT\n"
        f"余额：{new_balance:.4f} USDT"
    )
    await _safe_reply(update.message, text)
    logger.info(f"🔧 管理员手动充值 | 管理员: {admin_id} | 用户: {target_user_id} | 金额: {amount}")


def register(bot) -> None:
    bot.add_command("recharge", recharge_command)
    bot.add_command("balance", balance_command)
    bot.add_command("topup", topup_command)
    bot.add_callback_query(r"^check_balance$", check_balance_callback)
    bot.add_callback_query(r"^go_recharge$", go_recharge_callback)
