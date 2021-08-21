# -*- coding: utf-8 -*-
"""
本模块提供过滤器总线相关。
"""
import asyncio
import inspect
import logging
from typing import Any, Awaitable, Callable, Dict, List, Tuple

from mirai.bus import AbstractEventBus
from mirai.utils import PriorityDict
from mirai_extensions.trigger.filter import Filter

logger = logging.getLogger(__name__.replace('mirai_extensions', 'mirai'))

THandler = Callable[[Any, Any], Any]


class HandlerControl(AbstractEventBus):
    """事件接收控制器，通过 Filter 实现事件的过滤和解析。

    创建过滤器 `filter_` 后，可以通过 `hdc.on(filter_)` 装饰器注册处理器。

    处理器是一个函数，接受两个参数 `event` 和 `payload`。
    `event` 是接收到的原始事件，`payload` 是过滤器解析的结果。

    ```python
    hdc = HandlerControl(bot)

    @Filter(FriendMessage)
    async def filter_(event: FriendMessage):
        msg = str(event.message_chain)
        if msg.startswith('我是'):
            return msg[2:]

    @hdc.on(filter_)
    async def handler(event: FriendMessage, payload: str):
        ...
    ```
    """
    bus: AbstractEventBus

    def __init__(self, bus: AbstractEventBus, priority: int = 0):
        """
        Args:
            bus: 事件总线。
            priority: 事件接收控制器工作的优先级，小者优先。
        """
        self.bus = bus
        self.priority = priority
        self._handlers: Dict[Any, PriorityDict[Tuple[Filter, THandler]]] = {}

    def _new_handler(self, event_name):
        @self.bus.on(event_name, priority=self.priority)
        async def _(event):
            results = []
            for filters in self._handlers[event_name]:
                for filter_, func in list(filters):
                    payload = filter_.catch(event)
                    if payload is not None:
                        results.append(func(event, payload))
            return asyncio.gather(*filter(inspect.isawaitable, results))

    def subscribe(self, event: Filter, func: THandler, priority: int = 0):
        """注册一个过滤器的处理器。

        Args:
            event: 过滤器。
            func: 处理器。
            priority: 处理器的优先级，小者优先。
        """
        filter_ = event
        event_name = filter_.event_name
        if event_name not in self._handlers:
            self._handlers[event_name] = PriorityDict()
            self._new_handler(event_name)
        self._handlers[event_name].add(priority, (filter_, func))

    def unsubscribe(self, event: Filter, func: THandler):
        """取消一个过滤器的处理器。

        Args:
            event: 过滤器。
            func: 处理器。
        """
        try:
            self._handlers[event.event_name].remove((event, func))
        except KeyError:
            logger.warning(f'试图移除过滤器 `{event}` 的一个不存在的处理器 `{func}`。')

    def on(self, event: Filter, priority: int = 0):
        """以装饰器的形式注册一个过滤器的处理器。

        例如：
        ```python
        @hdc.on(filter)
        async def handler(event, payload):
            ...
        ```

        Args:
            event: 过滤器。
            priority: 处理器的优先级，小者优先。
        """
        def decorator(func: THandler) -> THandler:
            self.subscribe(event, func, priority)
            return func

        return decorator

    async def emit(self, event, *args, **kwargs) -> List[Awaitable[Any]]:
        """发送事件。

        Args:
            event: 事件名。
            *args: 发送的参数。
            **kwargs: 发送的参数。
        """
        return await self.bus.emit(event, *args, **kwargs)
