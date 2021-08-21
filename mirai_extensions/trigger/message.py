# -*- coding: utf-8 -*-

import logging
from typing import NewType, Optional, TypeVar, Union, cast

from mirai.models.entities import Friend, Group, GroupMember
from mirai.models.events import (
    FriendMessage, GroupMessage, MessageEvent, TempMessage
)
from mirai.models.message import MessageChain, Quote
from mirai.utils import async_
from mirai_extensions.trigger.filter import BaseFilter, TFilter, Filter

logger = logging.getLogger(__name__.replace('mirai_extensions', 'mirai'))

TEvent = TypeVar('TEvent')


class QuoteFilter(BaseFilter[MessageEvent]):
    quote: Optional[int]

    def __init__(self, quote: Union[MessageEvent, MessageChain, int]):
        if isinstance(quote, MessageEvent):
            quote = quote.message_chain
        if isinstance(quote, MessageChain):
            quote = quote.message_id
            self.quote = quote if quote >= 0 else None
        else:
            self.quote = quote

    def _catch(self, event: MessageEvent) -> Optional[MessageEvent]:
        if self.quote:
            quote = event.message_chain.get_first(Quote)
            if not quote or quote.id != self.quote:
                return None
        return event


class FriendFilter(BaseFilter[MessageEvent]):
    friend: int

    def __init__(self, friend: Union[Friend, int]):
        if isinstance(friend, Friend):
            friend = friend.id
        self.friend = friend

    def _catch(self, event: MessageEvent) -> Optional[MessageEvent]:
        if event.sender.id != self.friend:
            return None
        return event


TMessageEventWithGroup = Union[GroupMessage, TempMessage]


class GroupFilter(BaseFilter[TMessageEventWithGroup]):
    def __init__(self, group: Union[Group, int]):
        if isinstance(group, Group):
            group = group.id
        self.group = group

    def _catch(
        self, event: TMessageEventWithGroup
    ) -> Optional[TMessageEventWithGroup]:
        if event.group.id != self.group:
            return None
        return event


TNotSpecified = NewType("TNotSpecified", object)
_not_specified = TNotSpecified(object())


class GroupMemberFilter(BaseFilter[TMessageEventWithGroup]):
    def __init__(
        self,
        group_member: Union[GroupMember, int],
        group: Union[Group, int, TNotSpecified, None] = _not_specified,
    ):
        if isinstance(group_member, GroupMember):
            if group is _not_specified:
                group = group_member.group.id
            group_member = group_member.id

        mixin = [FriendFilter(group_member)]
        if group and group is not _not_specified:
            mixin.append(GroupFilter(cast(Union[Group, int], group)))
        super().__init__(mixin)


class FriendMessageFilter(Filter[FriendMessage]):
    """好友消息触发器。判断只接受指定好友发来的消息，或必需引用某条消息。"""
    def __init__(
        self,
        friend: Union[Friend, int, None] = None,
        quote: Union[MessageEvent, MessageChain, int, None] = None,
        func: Optional[TFilter[FriendMessage]] = None
    ):
        """
        Args:
            friend: 指定好友。
            quote: 指定引用某条消息。
            priority: 优先级，小者优先。
            filter: 过滤器。
        """
        mixin = []
        if friend:
            mixin.append(FriendFilter(friend))
        if quote:
            mixin.append(QuoteFilter(quote))

        super().__init__(FriendMessage, mixin, func)

        if quote:
            logger.warning(
                "FriendMessageTrigger 的 quote 参数目前由于不明原因，有时候不能正常使用，请注意。"
            )


class GroupMessageFilter(Filter[GroupMessage]):
    """群消息触发器。判断只接受指定群的某个群成员发来的消息，或必需引用某条消息。"""
    def __init__(
        self,
        group: Union[Group, int, TNotSpecified, None] = _not_specified,
        group_member: Union[GroupMember, int, None] = None,
        quote: Union[MessageEvent, MessageChain, int, None] = None,
        func: Optional[TFilter[GroupMessage]] = None
    ):
        """
        Args:
            group: 指定群。
            group_member: 指定群成员。
            quote: 指定引用某条消息。
            priority: 优先级，小者优先。
            filter: 过滤器。
        """
        mixin = []
        if group_member:
            mixin.append(GroupMemberFilter(group_member, group))
        elif group and group is not _not_specified:
            mixin.append(GroupFilter(cast(Union[Group, int], group)))
        if quote:
            mixin.append(QuoteFilter(quote))

        super().__init__(GroupMessage, mixin, func)


class TempMessageFilter(Filter[TempMessage]):
    """临时消息触发器。判断只接受指定群的某个群成员发来的消息，或必需引用某条消息。"""
    def __init__(
        self,
        group: Union[Group, int, TNotSpecified, None] = _not_specified,
        group_member: Union[GroupMember, int, None] = None,
        quote: Union[MessageEvent, MessageChain, int, None] = None,
        func: Optional[TFilter[TempMessage]] = None
    ):
        """
        Args:
            group: 指定群。
            group_member: 指定群成员。
            quote: 指定引用某条消息。
            priority: 优先级，小者优先。
            filter: 过滤器。
        """
        mixin = []
        if group_member:
            mixin.append(GroupMemberFilter(group_member, group))
        elif group and group is not _not_specified:
            mixin.append(GroupFilter(cast(Union[Group, int], group)))
        if quote:
            mixin.append(QuoteFilter(quote))

        super().__init__(GroupMessage, mixin, func)