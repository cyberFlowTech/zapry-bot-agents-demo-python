"""
群组功能数据管理（SQLite 版）
存储群组运势、排行榜、PK 对战等数据
"""

import json
import logging
from datetime import date, datetime
from typing import List, Optional

from db.database import db

logger = logging.getLogger(__name__)


class GroupDataManager:
    """管理群组相关数据"""

    # ===== 群日运势相关 =====

    def get_group_daily_fortune(self, group_id: str) -> Optional[dict]:
        """获取群今日运势"""
        today = str(date.today())
        row = db.fetch_one_sync(
            "SELECT fortune_data FROM group_fortunes WHERE group_id = ? AND fortune_date = ?",
            (group_id, today),
        )
        if row:
            return json.loads(row['fortune_data'])
        return None

    def set_group_daily_fortune(self, group_id: str, fortune: dict):
        """设置群今日运势"""
        today = str(date.today())
        fortune_json = json.dumps(fortune, ensure_ascii=False)
        db.execute_sync(
            """INSERT INTO group_fortunes (group_id, fortune_date, fortune_data)
               VALUES (?, ?, ?)
               ON CONFLICT(group_id, fortune_date) DO UPDATE SET
                 fortune_data = excluded.fortune_data
            """,
            (group_id, today, fortune_json),
        )

    # ===== 群排行榜相关 =====

    def add_user_divination(
        self,
        group_id: str,
        user_id: str,
        user_name: str,
        positive_count: int,
        cards: List[str],
    ):
        """添加用户占卜记录到排行榜"""
        today = str(date.today())
        cards_json = json.dumps(cards, ensure_ascii=False)

        db.execute_sync(
            """INSERT INTO group_rankings (group_id, user_id, user_name, positive_count, cards, ranking_date)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(group_id, user_id, ranking_date) DO UPDATE SET
                 user_name = excluded.user_name,
                 positive_count = excluded.positive_count,
                 cards = excluded.cards
            """,
            (group_id, user_id, user_name, positive_count, cards_json, today),
        )

    def get_group_ranking(self, group_id: str, date_str: Optional[str] = None) -> List[dict]:
        """获取群排行榜"""
        if date_str is None:
            date_str = str(date.today())

        rows = db.fetch_all_sync(
            """SELECT user_id, user_name, positive_count, cards
               FROM group_rankings
               WHERE group_id = ? AND ranking_date = ?
               ORDER BY positive_count DESC
            """,
            (group_id, date_str),
        )

        result = []
        for row in rows:
            result.append({
                'user_id': row['user_id'],
                'user_name': row['user_name'],
                'positive_count': row['positive_count'],
                'cards': json.loads(row['cards']),
            })
        return result

    def get_user_rank(self, group_id: str, user_id: str, date_str: Optional[str] = None) -> Optional[int]:
        """获取用户在群中的排名"""
        ranking = self.get_group_ranking(group_id, date_str)
        for idx, record in enumerate(ranking, 1):
            if record['user_id'] == user_id:
                return idx
        return None

    # ===== PK 记录相关 =====

    def add_pk_record(
        self,
        group_id: str,
        user1_id: str,
        user1_name: str,
        user1_cards: List[dict],
        user1_score: int,
        user2_id: str,
        user2_name: str,
        user2_cards: List[dict],
        user2_score: int,
        winner_id: str,
    ):
        """添加 PK 记录"""
        db.execute_sync(
            """INSERT INTO pk_records
               (group_id, user1_id, user1_name, user1_cards, user1_score,
                user2_id, user2_name, user2_cards, user2_score, winner_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                group_id,
                user1_id,
                user1_name,
                json.dumps(user1_cards, ensure_ascii=False),
                user1_score,
                user2_id,
                user2_name,
                json.dumps(user2_cards, ensure_ascii=False),
                user2_score,
                winner_id if winner_id != 'draw' else None,
            ),
        )

        # 保留最近 100 条（每个群）
        db.execute_sync(
            """DELETE FROM pk_records
               WHERE group_id = ? AND id NOT IN (
                 SELECT id FROM pk_records WHERE group_id = ?
                 ORDER BY id DESC LIMIT 100
               )
            """,
            (group_id, group_id),
        )

    def get_user_pk_stats(self, group_id: str, user_id: str) -> dict:
        """获取用户 PK 统计"""
        rows = db.fetch_all_sync(
            """SELECT winner_id FROM pk_records
               WHERE group_id = ? AND (user1_id = ? OR user2_id = ?)
            """,
            (group_id, user_id, user_id),
        )

        total = len(rows)
        wins = sum(1 for r in rows if r['winner_id'] == user_id)
        losses = total - wins
        win_rate = round(wins / total * 100, 1) if total > 0 else 0

        return {
            'total': total,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
        }


# 全局实例
group_manager = GroupDataManager()
