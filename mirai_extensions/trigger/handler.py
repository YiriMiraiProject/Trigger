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
    """事件接收控制器。"""
    bus: AbstractEventBus
    _handlers: Dict[Trigger, PriorityDict[Callable]]

    def __init__(self, bus: AbstractEventBus):
        self.bus = bus
        self._handlers = {}

    def subscribe(self, event: Trigger, func: Callable, priority: int = 0):
        trigger = event
        if event not in self._handlers:
            self._handlers[event] = PriorityDict()

            @self.bus.on(event.event_name, priority=event.priority)
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

        self._handlers[event].add(priority, func)

    def unsubscribe(self, event: Trigger, func: Callable):
        try:
            self._handlers[event].remove(func)
        except KeyError:
            logger.warning(f'试图移除触发器 `{event}` 的一个不存在的处理器 `{func}`。')

    def on(self, event: Trigger, priority: int = 0):
        """注册一个触发器。"""
        def decorator(func: Callable) -> Callable:
            self.subscribe(event, func, priority)
            return func

        return decorator

    async def emit(self, event, *args, **kwargs) -> List[Awaitable[Any]]:
        """发送事件。"""
        return await self.bus.emit(event, *args, **kwargs)
