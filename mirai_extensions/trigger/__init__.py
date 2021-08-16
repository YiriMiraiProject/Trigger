# -*- coding: utf-8 -*-
"""
事件触发器：提供更多处理事件的方式。
"""

__version__ = '0.2.0'
__author__ = '忘忧北萱草'

from mirai_extensions.trigger.handler import HandlerControl
from mirai_extensions.trigger.interrupt import InterruptControl
from mirai_extensions.trigger.message import (
    FriendMessageTrigger, GroupMessageTrigger, TempMessageTrigger
)
from mirai_extensions.trigger.trigger import Trigger

__all__ = [
    'Trigger', 'InterruptControl', 'HandlerControl', 'FriendMessageTrigger',
    'GroupMessageTrigger', 'TempMessageTrigger'
]
