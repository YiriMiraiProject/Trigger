# -*- coding: utf-8 -*-
"""
本模块提供触发器总线相关。
"""
import asyncio
import inspect
import logging
from typing import Any, Awaitable, Callable, Dict, List

from mirai.bus import AbstractEventBus
from mirai.utils import PriorityDict, async_
from mirai_extensions.trigger.trigger import Trigger

logger = logging.getLogger(__name__.replace('mirai_extensions', 'mirai'))


class HandlerControl(AbstractEventBus):
    """事件接收控制器，通过 Trigger 实现事件的过滤和解析。

    注册 trigger 后，可以通过 `hdc.on(trigger)` 装饰器注册处理器。

    处理器是一个函数，接受两个参数 `event` 和 `payload`。
    `event` 是接收到的原始事件，`payload` 是 trigger 的过滤器解析的结果。

    ```python
    hdc = HandlerControl(bot)

    @Trigger(FriendMessage)
    async def trigger(event: FriendMessage):
        msg = str(event.message_chain)
        if msg.startswith('我是'):
            return msg[2:]

    @hdc.on(trigger)
    async def handler(event: FriendMessage, payload: str):
        ...
    ```
    """
    bus: AbstractEventBus
    _handlers: Dict[Trigger, PriorityDict[Callable]]

    def __init__(self, bus: AbstractEventBus):
        """
        `bus: AbstractEventBus` 事件总线。
        """
        self.bus = bus
        self._handlers = {}

    def subscribe(self, event: Trigger, func: Callable, priority: int = 0):
        """注册一个触发器的处理器。

        `event: Trigger` 触发器。

        `func: Callable` 处理器。

        `priority: int` 处理器的优先级，小者优先。
        """
        trigger = event
        del event
        if trigger not in self._handlers:
            self._handlers[trigger] = PriorityDict()

            @self.bus.on(trigger.event_name, priority=trigger.priority)
            async def _(event):
                trigger.reset()
                if await trigger.catch(event):
                    payload = await trigger.wait()
                    results = []
                    for listeners in self._handlers[trigger]:
                        results += [
                            await async_(f(event, payload))
                            for f in list(listeners)
                        ]
                    return asyncio.gather(
                        *filter(inspect.isawaitable, results)
                    )

        self._handlers[trigger].add(priority, func)

    def unsubscribe(self, event: Trigger, func: Callable):
        """取消一个触发器的处理器。

        `event: Trigger` 触发器。

        `func: Callable` 处理器。
        """
        try:
            self._handlers[event].remove(func)
        except KeyError:
            logger.warning(f'试图移除触发器 `{event}` 的一个不存在的处理器 `{func}`。')

    def on(self, event: Trigger, priority: int = 0):
        """以装饰器的形式注册一个触发器的处理器。

        `event: Trigger` 触发器。

        `priority: int` 处理器的优先级，小者优先。

        例如：

        ```python
        @hdc.on(trigger)
        async def handler(event, payload):
            ...
        ```
        """
        def decorator(func: Callable) -> Callable:
            self.subscribe(event, func, priority)
            return func

        return decorator

    async def emit(self, event, *args, **kwargs) -> List[Awaitable[Any]]:
        """发送事件。

        `event` 事件名。

        `*args, **kwargs` 发送的参数。
        """
        return await self.bus.emit(event, *args, **kwargs)
