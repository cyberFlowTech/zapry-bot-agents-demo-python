"""
Zapry 平台全局兼容配置（向后兼容封装）。

底层实现已迁移至 zapry-bot-sdk，此文件保留原有接口供业务层使用。

已修复（2026-02 确认）：问题1(first_name),2(is_bot),5(私聊chat.id),6(chat.type),8(entities)
仍需兼容：问题3(ID字符串),4(username),7(g_前缀),9-14(API方法差异)
"""

import os
import sys
import re

# 确保 SDK 可导入
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SDK_PATH = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", "..", "related-codes", "zapry-bot-sdk-python"))
if os.path.isdir(SDK_PATH) and SDK_PATH not in sys.path:
    sys.path.insert(0, SDK_PATH)

try:
    from zapry_bot_sdk.utils.telegram_compat import ZapryCompat as _ZapryCompat
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False

from config import TG_PLATFORM

# 是否使用 Zapry 平台
IS_ZAPRY = (TG_PLATFORM == "zapry")

# Zapry 平台限制和特性
ZAPRY_LIMITATIONS = {
    "supports_markdown": False,
    "supports_edit_message": False,
    "supports_answer_callback": False,
    "supports_chat_action": False,
    "id_fields_are_strings": True,
    "group_id_has_prefix": True,
    "user_missing_username": True,
}

# 内部实例
if _SDK_AVAILABLE:
    _compat = _ZapryCompat(is_zapry=IS_ZAPRY)
else:
    _compat = None


def should_use_markdown() -> bool:
    """是否应该使用 Markdown 格式"""
    if _compat:
        return _compat.should_use_markdown()
    return not IS_ZAPRY


def should_edit_message() -> bool:
    """是否应该编辑消息（否则发送新消息）"""
    if _compat:
        return _compat.should_edit_message()
    return not IS_ZAPRY


def get_parse_mode():
    """获取应该使用的 parse_mode"""
    if _compat:
        return _compat.get_parse_mode()
    return None if IS_ZAPRY else "Markdown"


def clean_markdown(text: str) -> str:
    """
    清理文本中的 Markdown 标记。
    Zapry 平台不支持 Markdown 渲染。
    """
    if _compat:
        return _compat.clean_markdown(text)
    if not IS_ZAPRY:
        return text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    return text
