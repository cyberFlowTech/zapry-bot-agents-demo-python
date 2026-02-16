"""
群组功能 Handler
包含群日运势、PK对战、排行榜等功能
"""
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random
from datetime import datetime

from services.tarot_data import TarotDeck
from services.group_manager import group_manager

tarot_deck = TarotDeck()


# ===== 群日运势播报 =====

async def group_daily_fortune_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """群日运势播报命令"""
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("这个要在群里用哦~ 把我拉进群组就行 😊")
        return
    
    group_id = str(chat.id)
    existing_fortune = group_manager.get_group_daily_fortune(group_id)
    
    if existing_fortune:
        await _send_group_fortune(update, context, existing_fortune)
    else:
        fortune = _generate_group_fortune()
        group_manager.set_group_daily_fortune(group_id, fortune)
        await _send_group_fortune(update, context, fortune)


def _generate_group_fortune() -> dict:
    """生成群今日运势"""
    main_card = tarot_deck.draw_card()
    sub_card = tarot_deck.draw_card()
    
    positive_count = (1 if "正位" in main_card['orientation'] else 0) + \
                    (1 if "正位" in sub_card['orientation'] else 0)
    
    if positive_count == 2:
        stars = 5
        summary = "今天运势超棒！适合大胆尝试，万事皆可期~ ✨"
    elif positive_count == 1:
        stars = 3
        summary = "运势平稳的一天，稳扎稳打就好~"
    else:
        stars = 2
        summary = "今天可能会有些小波动，放慢脚步，顺其自然~"
    
    suitable_activities = _get_suitable_activities(main_card, sub_card)
    avoid_activities = _get_avoid_activities(main_card, sub_card)
    
    return {
        'main_card': {
            'name': main_card['name_full'],
            'meaning': main_card['meaning']
        },
        'sub_card': {
            'name': sub_card['name_full'],
            'meaning': sub_card['meaning']
        },
        'stars': stars,
        'summary': summary,
        'suitable': suitable_activities,
        'avoid': avoid_activities,
        'date': datetime.now().strftime('%Y年%m月%d日')
    }


def _get_suitable_activities(main_card: dict, sub_card: dict) -> List[str]:
    """根据牌面推荐适合的活动"""
    activities_pool = [
        "开展新项目", "团队协作", "创意讨论", "学习新知识",
        "社交活动", "规划未来", "处理重要事务", "寻求建议"
    ]
    
    positive_count = (1 if "正位" in main_card['orientation'] else 0) + \
                    (1 if "正位" in sub_card['orientation'] else 0)
    
    if positive_count >= 1:
        return random.sample(activities_pool, min(3, len(activities_pool)))
    else:
        return random.sample(activities_pool[:4], 2)


def _get_avoid_activities(main_card: dict, sub_card: dict) -> List[str]:
    """根据牌面提示需要避免的事情"""
    avoid_pool = [
        "冲动决策", "消极情绪", "过度承诺", "忽视细节",
        "孤立行动", "盲目跟风", "保守主义", "过度焦虑"
    ]
    
    positive_count = (1 if "正位" in main_card['orientation'] else 0) + \
                    (1 if "正位" in sub_card['orientation'] else 0)
    
    if positive_count == 0:
        return random.sample(avoid_pool, 3)
    else:
        return random.sample(avoid_pool, 2)


async def _send_group_fortune(update: Update, context: ContextTypes.DEFAULT_TYPE, fortune: dict):
    """发送群运势消息"""
    stars_display = "⭐" * fortune['stars']
    
    message = (
        f"🌅 今日群运势\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📅 {fortune['date']}\n"
        f"🏰 {update.effective_chat.title or '本群'}\n\n"
        f"🔮 今日塔罗气象\n"
        f"   主牌：{fortune['main_card']['name']}\n"
        f"   副牌：{fortune['sub_card']['name']}\n\n"
        f"📊 运势指数：{stars_display} {fortune['stars']}/5\n\n"
        f"💭 {fortune['summary']}\n\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"✅ 今日适合\n"
    )
    
    for activity in fortune['suitable']:
        message += f"   • {activity}\n"
    
    message += f"\n❌ 今日留心\n"
    for activity in fortune['avoid']:
        message += f"   • {activity}\n"
    
    ranking = group_manager.get_group_ranking(str(update.effective_chat.id))
    participant_count = len(ranking)
    
    message += (
        f"\n━━━━━━━━━━━━━━━━━\n\n"
        f"👥 已有 {participant_count} 人查看了今天的运势\n\n"
        f"想看自己的运势？发 /tarot 加上问题~\n"
        f"想看排行？发 /ranking 🏆"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎴 抽我的运势", callback_data='my_daily_fortune'),
            InlineKeyboardButton("🏆 看排行", callback_data='show_ranking')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)


# ===== 群排行榜 =====

async def ranking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示群排行榜"""
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("这个要在群里用哦~")
        return
    
    group_id = str(chat.id)
    ranking = group_manager.get_group_ranking(group_id)
    
    if not ranking:
        await update.message.reply_text(
            "今天还没有人占卜呢~\n\n"
            "发 /tarot 加上问题来一次，你的结果会自动上榜 🏆"
        )
        return
    
    message = (
        f"🏆 今日运势排行榜\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📅 {datetime.now().strftime('%Y年%m月%d日')}\n"
        f"🏰 {chat.title or '本群'}\n\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
    )
    
    medals = ["👑", "🥈", "🥉"]
    
    for idx, record in enumerate(ranking[:10], 1):
        medal = medals[idx-1] if idx <= 3 else f"{idx}."
        user_name = record['user_name']
        positive = record['positive_count']
        cards_display = " ".join(["🎴" for _ in record['cards']])
        
        message += f"{medal} {user_name} - {positive}张正位\n"
        message += f"   {cards_display}\n\n"
    
    total_participants = len(ranking)
    message += (
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📊 共 {total_participants} 人参与\n\n"
        f"发 /tarot 加上问题也来参与吧~"
    )
    
    await update.message.reply_text(message)


# ===== PK对战 =====

async def pk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """发起塔罗PK对战"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("PK 要在群里玩哦~")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "⚔️ 塔罗对决\n\n"
            "回复你想挑战的人的消息，然后发 /pk\n\n"
            "双方会同时抽三张牌，比拼牌面能量~ 🎴"
        )
        return
    
    opponent = update.message.reply_to_message.from_user
    
    if opponent.id == user.id:
        await update.message.reply_text("不能和自己对战哦~ 😅")
        return
    
    if opponent.is_bot:
        await update.message.reply_text("机器人不会玩塔罗啦~ 🤖")
        return
    
    message = (
        f"⚔️ 塔罗对决\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"👤 {user.first_name} 向 {opponent.first_name} 发起挑战！\n\n"
        f"双方将同时抽取三张牌，比拼牌面能量~\n\n"
        f"🎴 等待 {opponent.first_name} 接受挑战..."
    )
    
    pk_id = f"{chat.id}_{user.id}_{opponent.id}_{datetime.now().timestamp()}"
    context.bot_data[pk_id] = {
        'group_id': chat.id,
        'challenger_id': user.id,
        'challenger_name': user.first_name,
        'opponent_id': opponent.id,
        'opponent_name': opponent.first_name,
        'status': 'pending'
    }
    
    keyboard = [
        [
            InlineKeyboardButton("✅ 接受挑战", callback_data=f'accept_pk_{pk_id}'),
            InlineKeyboardButton("❌ 算了", callback_data=f'reject_pk_{pk_id}')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)


async def accept_pk_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接受PK挑战"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    pk_id = query.data.replace('accept_pk_', '')
    
    if pk_id not in context.bot_data:
        try:
            await query.edit_message_text("这场对决已经结束了~")
        except Exception:
            pass
        return
    
    pk_info = context.bot_data[pk_id]
    
    if query.from_user.id != pk_info['opponent_id']:
        try:
            await query.answer("只有被挑战的人才能接受哦~", show_alert=True)
        except Exception:
            pass
        return
    
    await _execute_pk_battle(query, context, pk_info)
    del context.bot_data[pk_id]


async def reject_pk_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """拒绝PK挑战"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    pk_id = query.data.replace('reject_pk_', '')
    
    if pk_id not in context.bot_data:
        try:
            await query.edit_message_text("这场对决已经结束了~")
        except Exception:
            pass
        return
    
    pk_info = context.bot_data[pk_id]
    
    if query.from_user.id != pk_info['opponent_id']:
        try:
            await query.answer("只有被挑战的人才能拒绝哦~", show_alert=True)
        except Exception:
            pass
        return
    
    message = (
        f"━━━━━━━━━━━━━━━━━\n"
        f"{pk_info['opponent_name']} 拒绝了挑战\n"
        f"━━━━━━━━━━━━━━━━━"
    )
    
    try:
        await query.edit_message_text(message)
    except Exception:
        await context.bot.send_message(chat_id=query.message.chat.id, text=message)
    
    del context.bot_data[pk_id]


async def _execute_pk_battle(query, context, pk_info: dict):
    """执行PK对战"""
    user1_spread = tarot_deck.get_three_card_spread()
    user2_spread = tarot_deck.get_three_card_spread()
    
    def calculate_score(spread):
        score = 0
        for card in spread:
            if "正位" in card['orientation']:
                score += 30
            else:
                score += 15
        return score
    
    user1_score = calculate_score(user1_spread)
    user2_score = calculate_score(user2_spread)
    
    if user1_score > user2_score:
        winner_id = pk_info['challenger_id']
        winner_name = pk_info['challenger_name']
        result_text = f"🏆 胜者：{winner_name}"
    elif user2_score > user1_score:
        winner_id = pk_info['opponent_id']
        winner_name = pk_info['opponent_name']
        result_text = f"🏆 胜者：{winner_name}"
    else:
        winner_id = None
        winner_name = None
        result_text = "🤝 平局！势均力敌！"
    
    message = (
        f"⚔️ 塔罗对决结果\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"👤 {pk_info['challenger_name']} VS {pk_info['opponent_name']}\n\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"🎴 {pk_info['challenger_name']} 的牌：\n"
    )
    
    for card in user1_spread:
        message += f"   • {card['name_full']}\n"
    
    message += f"💪 能量值: {user1_score}分\n\n"
    
    message += f"🎴 {pk_info['opponent_name']} 的牌：\n"
    
    for card in user2_spread:
        message += f"   • {card['name_full']}\n"
    
    message += f"💪 能量值: {user2_score}分\n\n"
    
    message += (
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"{result_text}\n\n"
    )
    
    # 晚晴点评
    if winner_id:
        if abs(user1_score - user2_score) > 20:
            comment = f"{winner_name} 的牌阵能量远超对手，今天运势正盛呢~ ✨"
        else:
            comment = f"{winner_name} 略胜一筹，不过双方实力很接近，精彩的对决~"
    else:
        comment = "双方能量完全一致，这可是很少见的巧合呢~ 🌙"
    
    message += f"🔮 晚晴点评\n{comment}"
    
    group_manager.add_pk_record(
        str(pk_info['group_id']),
        str(pk_info['challenger_id']),
        pk_info['challenger_name'],
        [{'name': c['name_full']} for c in user1_spread],
        user1_score,
        str(pk_info['opponent_id']),
        pk_info['opponent_name'],
        [{'name': c['name_full']} for c in user2_spread],
        user2_score,
        str(winner_id) if winner_id else 'draw'
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔁 再战一局", callback_data='new_pk'),
            InlineKeyboardButton("📊 我的战绩", callback_data='my_pk_stats')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(message, reply_markup=reply_markup)
    except Exception:
        await context.bot.send_message(
            chat_id=query.message.chat.id, text=message, reply_markup=reply_markup
        )


# ===== 回调处理器 =====

async def my_daily_fortune_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """抽取个人今日运势"""
    query = update.callback_query
    try:
        await query.answer("正在为你抽取运势...")
    except Exception:
        pass
    
    default_question = "我今天运势如何？"
    context.user_data['tarot_question'] = default_question
    
    keyboard = [
        [InlineKeyboardButton("🎴 抽牌", callback_data='draw_tarot')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        f"🔮 问题：{default_question}\n\n"
        f"在心中默念你的问题~\n"
        f"准备好了就点下面的按钮 🎴",
        reply_markup=reply_markup,
    )


async def show_ranking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示排行榜回调"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    group_id = str(query.message.chat.id)
    ranking = group_manager.get_group_ranking(group_id)
    
    if not ranking:
        await query.message.reply_text("今天还没有人占卜呢~")
        return
    
    message = f"🏆 今日 TOP5\n\n"
    
    medals = ["👑", "🥈", "🥉", "4️⃣", "5️⃣"]
    for idx, record in enumerate(ranking[:5], 1):
        message += f"{medals[idx-1]} {record['user_name']} - {record['positive_count']}张正位\n"
    
    message += f"\n发 /ranking 看完整排行~"
    
    await query.message.reply_text(message)


async def my_pk_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看个人PK战绩"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    user_id = str(query.from_user.id)
    group_id = str(query.message.chat.id)
    
    stats = group_manager.get_user_pk_stats(group_id, user_id)
    
    message = (
        f"📊 {query.from_user.first_name} 的战绩\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"⚔️ 总场次：{stats['total']}场\n"
        f"✅ 胜利：{stats['wins']}场\n"
        f"❌ 失败：{stats['losses']}场\n"
        f"📈 胜率：{stats['win_rate']}%\n\n"
    )
    
    if stats['total'] == 0:
        message += "还没有对战记录呢，快去挑战朋友吧~ ⚔️"
    elif stats['win_rate'] >= 70:
        message += "塔罗战神，所向披靡！👑"
    elif stats['win_rate'] >= 50:
        message += "实力强劲，继续加油~ ⚔️"
    else:
        message += "越挫越勇，胜利在望~ 💪"
    
    await query.message.reply_text(message)


def register(bot) -> None:
    bot.add_command("group_fortune", group_daily_fortune_command)
    bot.add_command("ranking", ranking_command)
    bot.add_command("pk", pk_command)
    bot.add_callback_query(r"^accept_pk_", accept_pk_callback)
    bot.add_callback_query(r"^reject_pk_", reject_pk_callback)
    bot.add_callback_query(r"^my_daily_fortune$", my_daily_fortune_callback)
    bot.add_callback_query(r"^show_ranking$", show_ranking_callback)
    bot.add_callback_query(r"^my_pk_stats$", my_pk_stats_callback)
