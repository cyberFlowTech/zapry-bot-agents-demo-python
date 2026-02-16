"""
塔罗占卜历史管理（SQLite 版）
- 持久化存储用户的占卜记录
- 替代之前 context.user_data['tarot_history'] 的内存存储
- 提供 AI 上下文格式化
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from db.database import db

logger = logging.getLogger(__name__)


class TarotHistoryManager:
    """塔罗占卜历史管理器"""

    MAX_READINGS_PER_USER = 20  # 每用户最多保留 20 条记录

    async def save_reading(
        self,
        user_id: str,
        question: str,
        cards: list,
        interpretation: str,
    ) -> bool:
        """
        保存一次占卜记录

        Args:
            user_id: 用户 ID
            question: 占卜问题
            cards: 牌面列表 [{"position":"过去","card":"...","meaning":"..."}]
            interpretation: 解读文本
        """
        try:
            cards_json = json.dumps(cards, ensure_ascii=False)

            await db.execute(
                """INSERT INTO tarot_readings (user_id, question, cards, interpretation)
                   VALUES (?, ?, ?, ?)
                """,
                (user_id, question, cards_json, interpretation[:1000]),
            )

            # 保留最近 N 条：先查第 N 条的 id，再删除更早的
            cutoff = await db.fetch_one(
                """SELECT id FROM tarot_readings
                   WHERE user_id = ?
                   ORDER BY id DESC
                   LIMIT 1 OFFSET ?
                """,
                (user_id, self.MAX_READINGS_PER_USER),
            )
            if cutoff:
                await db.execute(
                    "DELETE FROM tarot_readings WHERE user_id = ? AND id <= ?",
                    (user_id, cutoff['id']),
                )

            logger.info(f"💾 保存塔罗记录 | 用户: {user_id} | 问题: {question[:30]}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存塔罗记录失败 | 用户: {user_id} | {e}")
            return False

    async def get_recent_readings(self, user_id: str, limit: int = 5) -> List[dict]:
        """获取用户最近的占卜记录"""
        rows = await db.fetch_all(
            """SELECT question, cards, interpretation, created_at
               FROM tarot_readings
               WHERE user_id = ?
               ORDER BY id DESC
               LIMIT ?
            """,
            (user_id, limit),
        )

        readings = []
        for row in rows:
            readings.append({
                'timestamp': row['created_at'],
                'question': row['question'],
                'cards': json.loads(row['cards']),
                'interpretation': row['interpretation'],
            })

        # 按时间正序排列（最旧的在前）
        readings.reverse()
        return readings

    async def get_reading_count(self, user_id: str) -> int:
        """获取用户的占卜总次数"""
        row = await db.fetch_one(
            "SELECT COUNT(*) as cnt FROM tarot_readings WHERE user_id = ?",
            (user_id,),
        )
        return row['cnt'] if row else 0

    async def delete_user_readings(self, user_id: str) -> bool:
        """删除用户所有占卜记录"""
        try:
            await db.execute(
                "DELETE FROM tarot_readings WHERE user_id = ?",
                (user_id,),
            )
            logger.info(f"🗑️ 删除塔罗记录 | 用户: {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 删除塔罗记录失败 | 用户: {user_id} | {e}")
            return False

    # ------------------------------------------------------------------
    # 格式化（给 AI 用）
    # ------------------------------------------------------------------

    @staticmethod
    def _humanize_time(timestamp_str: str) -> str:
        """
        将时间戳转换为人类自然语言描述
        例如：
          3分钟前 → "刚刚"
          40分钟前 → "40分钟前"
          2小时前 → "今天下午"
          昨天 → "昨天"
          3天前 → "3天前"
          2周前 → "大约两周前"
        """
        try:
            ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            try:
                ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
            except (ValueError, TypeError):
                return timestamp_str

        now = datetime.now()
        diff = now - ts
        total_seconds = diff.total_seconds()
        total_minutes = total_seconds / 60
        total_hours = total_seconds / 3600
        total_days = diff.days

        if total_minutes < 5:
            return "刚刚"
        elif total_minutes < 30:
            return f"{int(total_minutes)}分钟前"
        elif total_minutes < 60:
            return "半小时前"
        elif total_hours < 2:
            return "1小时前"
        elif total_days == 0:
            # 今天的，显示具体时段
            hour = ts.hour
            if hour < 6:
                period = "今天凌晨"
            elif hour < 12:
                period = "今天上午"
            elif hour < 14:
                period = "今天中午"
            elif hour < 18:
                period = "今天下午"
            else:
                period = "今天晚上"
            return period
        elif total_days == 1:
            return "昨天"
        elif total_days == 2:
            return "前天"
        elif total_days <= 7:
            return f"{total_days}天前"
        elif total_days <= 14:
            return "大约一周前"
        elif total_days <= 30:
            weeks = total_days // 7
            return f"大约{weeks}周前"
        elif total_days <= 60:
            return "大约一个月前"
        else:
            months = total_days // 30
            return f"大约{months}个月前"

    @staticmethod
    def format_readings_for_ai(readings: List[dict]) -> str:
        """
        将塔罗历史格式化为 AI 可读文本
        包含人性化的相对时间描述，帮助 AI 准确表达时间关系
        """
        if not readings:
            return ""

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        formatted = f"【用户的塔罗占卜历史】（当前时间: {now_str}）\n\n"

        for i, reading in enumerate(readings, 1):
            # 生成人性化时间描述
            relative_time = TarotHistoryManager._humanize_time(reading['timestamp'])
            formatted += f"占卜 {i}（{relative_time}，{reading['timestamp']}）:\n"
            formatted += f"问题: {reading['question']}\n"
            formatted += "牌面:\n"
            for card_info in reading['cards']:
                formatted += f"  • {card_info['position']}: {card_info['card']}\n"
            interp = reading.get('interpretation', '')
            if interp:
                formatted += f"解读: {interp[:200]}...\n\n"

        formatted += (
            "【重要提醒】引用占卜记录时，请根据上面的相对时间自然表达：\n"
            "  - 如果是「刚刚」或「几分钟前」→ 说「你刚才占的那次」「刚才的牌面」\n"
            "  - 如果是「今天上午/下午」→ 说「你今天上午那次占卜」\n"
            "  - 如果是「昨天」→ 说「你昨天占的」\n"
            "  - 如果是「几天前」→ 说「你前几天占的」\n"
            "  - 不要笼统地说「我记得你之前」「你上次」，要用具体的时间感\n"
        )
        return formatted


# 导出单例
tarot_history_manager = TarotHistoryManager()
