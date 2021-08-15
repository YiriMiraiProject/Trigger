# -*- coding: utf-8 -*-

from typing import NewType, Optional, Union, cast

from mirai.models.entities import Friend, Group, GroupMember
from mirai.models.events import (
    FriendMessage, GroupMessage, MessageEvent, TempMessage
)
from mirai.models.message import MessageChain, Quote
from mirai.utils import async_
from mirai_extensions.trigger.trigger import TFilter, Trigger


class FriendMessageTrigger(Trigger[FriendMessage]):
    """好友消息触发器。判断只接受指定好友发来的消息，或必需引用某条消息。"""
    friend: Optional[int]
    """指定好友。"""
    quote: Optional[int]
    """指定引用某条消息。"""
    custom_filter: Optional[TFilter[FriendMessage]]
    """过滤器。"""
    def __init__(
        self,
        friend: Union[Friend, int, None] = None,
        quote: Union[MessageEvent, MessageChain, int, None] = None,
        priority: int = 0,
        filter: Optional[TFilter[FriendMessage]] = None
    ):
        """
        Args:
            friend (`Union[Friend, int, None]`): 指定好友。
            quote (`Union[MessageEvent, MessageChain, int, None]`): 指定引用某条消息。
            priority (`int`): 优先级，小者优先。
            filter (`Optional[TFilter[FriendMessage]]`): 过滤器。
        """
        super().__init__(FriendMessage, priority, filter)

        if isinstance(friend, Friend):
            friend = friend.id
        self.friend = friend

        if isinstance(quote, MessageEvent):
            quote = quote.message_chain
        if isinstance(quote, MessageChain):
            quote = quote.message_id
            self.quote = quote if quote >= 0 else None
        else:
            self.quote = quote

    async def _filter(self, event: FriendMessage):
        if self.friend and event.sender.id != self.friend:
            return
        if self.quote:
            quotes = event.message_chain[Quote, 1]
            if not quotes or Quote[0].id != self.quote:
                return
        if self.custom_filter:
            return await async_(self.custom_filter(event))

    def set_filter(self, filter: TFilter[FriendMessage]):
        self.custom_filter = filter
        return super().set_filter(self._filter)


TNotSpecified = NewType("TNotSpecified", object)
_not_specified = TNotSpecified(object())


class GroupMessageTrigger(Trigger[GroupMessage]):
    """群消息触发器。判断只接受指定群的某个群成员发来的消息，或必需引用某条消息。"""
    group: Optional[int]
    """指定群。"""
    group_member: Optional[int]
    """指定群成员。"""
    quote: Optional[int]
    """指定引用某条消息。"""
    custom_filter: Optional[TFilter[GroupMessage]]
    """过滤器。"""
    def __init__(
        self,
        group: Union[Group, int, TNotSpecified, None] = _not_specified,
        group_member: Union[GroupMember, int, None] = None,
        quote: Union[MessageEvent, MessageChain, int, None] = None,
        priority: int = 0,
        filter: Optional[TFilter[GroupMessage]] = None
    ):
        """
        Args:
            group (`Union[Group, int, None]`): 指定群。
            group_member (`Union[GroupMember, int, None]`): 指定群成员。
            quote (`Union[MessageEvent, MessageChain, int, None]`): 指定引用某条消息。
            priority (`int`): 优先级，小者优先。
            filter (`Optional[TFilter[GroupMessage]]`): 过滤器。
        """
        super().__init__(GroupMessage, priority, filter)

        if isinstance(group_member, GroupMember):
            if group is _not_specified:
                group = group_member.group.id
            group_member = group_member.id
        self.group_member = group_member

        if isinstance(group, Group):
            group = group.id
        elif group is _not_specified:
            group = None
        self.group = cast(Optional[int], group)

        if isinstance(quote, MessageEvent):
            quote = quote.message_chain
        if isinstance(quote, MessageChain):
            quote = quote.message_id
            self.quote = quote if quote >= 0 else None
        else:
            self.quote = quote

    async def _filter(self, event: GroupMessage):
        if self.group and event.group.id != self.group:
            return
        if self.group_member and event.sender.id != self.group_member:
            return
        if self.quote:
            quotes = event.message_chain[Quote, 1]
            if not quotes or Quote[0].id != self.quote:
                return
        if self.custom_filter:
            return await async_(self.custom_filter(event))

    def set_filter(self, filter: TFilter[GroupMessage]):
        self.custom_filter = filter
        return super().set_filter(self._filter)


class TempMessageTrigger(Trigger[TempMessage]):
    """临时消息触发器。判断只接受指定群的某个群成员发来的消息，或必需引用某条消息。"""
    group: Optional[int]
    """指定群。"""
    group_member: Optional[int]
    """指定群成员。"""
    quote: Optional[int]
    """指定引用某条消息。"""
    custom_filter: Optional[TFilter[TempMessage]]
    """过滤器。"""
    def __init__(
        self,
        group: Union[Group, int, TNotSpecified, None] = _not_specified,
        group_member: Union[GroupMember, int, None] = None,
        quote: Union[MessageEvent, MessageChain, int, None] = None,
        priority: int = 0,
        filter: Optional[TFilter[TempMessage]] = None
    ):
        """
        Args:
            group (`Union[Group, int, None]`): 指定群。
            group_member (`Union[GroupMember, int, None]`): 指定群成员。
            quote (`Union[MessageEvent, MessageChain, int, None]`): 指定引用某条消息。
            priority (`int`): 优先级，小者优先。
            filter (`Optional[TFilter[TempMessage]]`): 过滤器。
        """
        super().__init__(TempMessage, priority, filter)

        if isinstance(group_member, GroupMember):
            if group is _not_specified:
                group = group_member.group.id
            group_member = group_member.id
        self.group_member = group_member

        if isinstance(group, Group):
            group = group.id
        elif group is _not_specified:
            group = None
        self.group = cast(Optional[int], group)

        if isinstance(quote, MessageEvent):
            quote = quote.message_chain
        if isinstance(quote, MessageChain):
            quote = quote.message_id
            self.quote = quote if quote >= 0 else None
        else:
            self.quote = quote

    async def _filter(self, event: TempMessage):
        if self.group and event.group.id != self.group:
            return
        if self.group_member and event.sender.id != self.group_member:
            return
        if self.quote:
            quotes = event.message_chain[Quote, 1]
            if not quotes or Quote[0].id != self.quote:
                return
        if self.custom_filter:
            return await async_(self.custom_filter(event))

    def set_filter(self, filter: TFilter[TempMessage]):
        self.custom_filter = filter
        return super().set_filter(self._filter)
