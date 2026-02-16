"""
对话历史管理（SQLite 版）
- 持久化存储用户的短期对话历史
- 替代 context.user_data['conversation_history']（重启丢失）
- 为 AI 提供连贯的上下文
"""

import json
import logging
from typing import List, Optional

from db.database import db

logger = logging.getLogger(__name__)

# 建表 SQL（追加到现有数据库）
_CREATE_CHAT_HISTORY_SQL = """
CREATE TABLE IF NOT EXISTS chat_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL,
    role        TEXT NOT NULL,       -- 'user' 或 'assistant'
    content     TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id);
"""


class ChatHistoryManager:
    """对话历史管理器"""

    MAX_MESSAGES_PER_USER = 40  # 每用户保留最近 40 条消息（约 20 轮对话）

    def ensure_table(self):
        """确保表存在（幂等）"""
        conn = db._get_conn()
        conn.executescript(_CREATE_CHAT_HISTORY_SQL)
        conn.commit()

    async def add_message(self, user_id: str, role: str, content: str) -> None:
        """添加一条对话消息"""
        await db.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )

        # 保留最近 N 条：先查第 N 条的 id，再删除更早的（比子查询快很多）
        cutoff = await db.fetch_one(
            """SELECT id FROM chat_history
               WHERE user_id = ?
               ORDER BY id DESC
               LIMIT 1 OFFSET ?
            """,
            (user_id, self.MAX_MESSAGES_PER_USER),
        )
        if cutoff:
            await db.execute(
                "DELETE FROM chat_history WHERE user_id = ? AND id <= ?",
                (user_id, cutoff['id']),
            )

    async def get_history(self, user_id: str, limit: int = 40) -> List[dict]:
        """
        获取用户的对话历史（用于传给 OpenAI）
        返回格式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        rows = await db.fetch_all(
            """SELECT role, content FROM chat_history
               WHERE user_id = ?
               ORDER BY id DESC
               LIMIT ?
            """,
            (user_id, limit),
        )

        # 反转为正序（最旧的在前）
        history = [{"role": r['role'], "content": r['content']} for r in reversed(rows)]
        return history

    async def clear_history(self, user_id: str) -> None:
        """清空用户的对话历史"""
        await db.execute(
            "DELETE FROM chat_history WHERE user_id = ?",
            (user_id,),
        )
        logger.info(f"🗑️ 对话历史已清除 | 用户: {user_id}")

    def clear_history_sync(self, user_id: str) -> None:
        """同步清空（用于 /clear, /forget）"""
        db.execute_sync(
            "DELETE FROM chat_history WHERE user_id = ?",
            (user_id,),
        )

    async def get_message_count(self, user_id: str) -> int:
        """获取消息总数"""
        row = await db.fetch_one(
            "SELECT COUNT(*) as cnt FROM chat_history WHERE user_id = ?",
            (user_id,),
        )
        return row['cnt'] if row else 0


# 导出单例
chat_history_manager = ChatHistoryManager()
