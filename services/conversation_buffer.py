"""
对话缓冲区（SQLite 版）
- 持久化存储：重启后缓冲区不丢失
- asyncio.Lock 并发保护：防止同一用户的竞态条件
- 基于数据库行计数触发提取，不再依赖内存 LRU
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

from db.database import db

logger = logging.getLogger(__name__)


class ConversationBuffer:
    """对话缓冲区管理器（SQLite 版）"""

    def __init__(self):
        # 每个用户独立的锁（仍用内存，锁不需要持久化）
        self._locks: dict = {}

        # ---------- 配置 ----------
        self.EXTRACTION_TRIGGER_COUNT = 5    # 每 N 条触发一次提取
        self.EXTRACTION_TRIGGER_HOURS = 24   # 或距上次提取超过 N 小时

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _get_lock(self, user_id: str) -> asyncio.Lock:
        """获取用户级别的锁（懒创建）"""
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    async def add_message(self, user_id: str, role: str, content: str) -> None:
        """添加消息到缓冲区"""
        async with self._get_lock(user_id):
            await db.execute(
                "INSERT INTO conversation_buffer (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content),
            )
            logger.debug(f"📝 缓冲区 +1 | 用户: {user_id}")

    async def should_extract(self, user_id: str) -> bool:
        """
        判断是否触发记忆提取

        触发条件（满足任一）：
        1. 缓冲区消息数 >= EXTRACTION_TRIGGER_COUNT
        2. 距上次提取 >= EXTRACTION_TRIGGER_HOURS 且缓冲区不为空
        """
        async with self._get_lock(user_id):
            # 查询缓冲区消息数
            row = await db.fetch_one(
                "SELECT COUNT(*) as cnt FROM conversation_buffer WHERE user_id = ?",
                (user_id,),
            )
            count = row['cnt'] if row else 0

            if count == 0:
                return False

            # 条件 1：消息数达到阈值
            if count >= self.EXTRACTION_TRIGGER_COUNT:
                logger.info(
                    f"🔔 触发提取 | 用户: {user_id} | "
                    f"原因: 对话数 {count} >= {self.EXTRACTION_TRIGGER_COUNT}"
                )
                return True

            # 条件 2：距上次提取超过阈值时间
            ext_row = await db.fetch_one(
                "SELECT last_extraction FROM extraction_log WHERE user_id = ?",
                (user_id,),
            )
            if ext_row and ext_row['last_extraction']:
                last_time = datetime.strptime(ext_row['last_extraction'], '%Y-%m-%d %H:%M:%S')
                hours = (datetime.now() - last_time).total_seconds() / 3600
                if hours >= self.EXTRACTION_TRIGGER_HOURS:
                    logger.info(
                        f"🔔 触发提取 | 用户: {user_id} | "
                        f"原因: 距上次已 {hours:.1f}h"
                    )
                    return True

            return False

    async def get_and_clear(self, user_id: str) -> list:
        """
        获取待处理的对话并清空缓冲区（原子操作）
        """
        async with self._get_lock(user_id):
            # 读取所有缓冲消息
            rows = await db.fetch_all(
                "SELECT role, content, created_at as timestamp FROM conversation_buffer "
                "WHERE user_id = ? ORDER BY id ASC",
                (user_id,),
            )

            if not rows:
                return []

            # 转换格式
            conversations = [
                {"role": r['role'], "content": r['content'], "timestamp": r['timestamp']}
                for r in rows
            ]

            # 清空缓冲区
            await db.execute(
                "DELETE FROM conversation_buffer WHERE user_id = ?",
                (user_id,),
            )

            # 更新提取记录
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await db.execute(
                """INSERT INTO extraction_log (user_id, last_extraction, extraction_count)
                   VALUES (?, ?, 1)
                   ON CONFLICT(user_id) DO UPDATE SET
                     last_extraction = excluded.last_extraction,
                     extraction_count = extraction_count + 1
                """,
                (user_id, now),
            )

            logger.info(
                f"🧠 取出缓冲区 | 用户: {user_id} | 共 {len(conversations)} 条"
            )
            return conversations

    async def clear_buffer(self, user_id: str) -> None:
        """清空用户的缓冲区"""
        async with self._get_lock(user_id):
            await db.execute(
                "DELETE FROM conversation_buffer WHERE user_id = ?",
                (user_id,),
            )

    def clear_buffer_sync(self, user_id: str) -> None:
        """同步版本的清空（用于 /forget 等场景）"""
        db.execute_sync(
            "DELETE FROM conversation_buffer WHERE user_id = ?",
            (user_id,),
        )
        self._locks.pop(user_id, None)

    async def get_buffer_size(self, user_id: str) -> int:
        """获取缓冲区消息数量"""
        row = await db.fetch_one(
            "SELECT COUNT(*) as cnt FROM conversation_buffer WHERE user_id = ?",
            (user_id,),
        )
        return row['cnt'] if row else 0


# 导出单例
conversation_buffer = ConversationBuffer()
