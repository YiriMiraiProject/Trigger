# -*- coding: utf-8 -*-
"""
本模块提供中断控制器相关。
"""
import asyncio
import logging
from typing import Any, Dict

from mirai.bus import AbstractEventBus
from mirai.utils import PriorityDict
from mirai_extensions.trigger.trigger import Trigger

logger = logging.getLogger(__name__.replace('mirai_extensions', 'mirai'))


class InterruptControl:
    """中断控制器。"""
    def __init__(self, bus: AbstractEventBus, priority: int = 15):
        self.bus = bus
        self._triggers: Dict[Any, PriorityDict[Trigger]] = {}
        self.priority = priority

    def _new_handler(self, event_name):
        @self.bus.on(event_name, priority=self.priority)
        async def _(event):
            async def catch_event(trigger: Trigger) -> bool:
                return await trigger.catch(event)

            for triggers in self._triggers[event_name]:
                for trigger in list(triggers):
                    if await catch_event(trigger):
                        break
                else:  # 跳出两重循环
                    continue
                break

    async def wait(self, trigger: Trigger, timeout: float = 0.):
        event_name = trigger.event_name

        if event_name not in self._triggers:
            self._triggers[event_name] = PriorityDict()
            self._new_handler(event_name)

        self._triggers[event_name].add(trigger.priority, trigger)

        @trigger.add_done_callback
        def _(_: asyncio.Future):
            self._triggers[event_name].remove(trigger)

        logger.debug(f'[InterruptControl] 等待触发器 {trigger}。')
        return await trigger.wait(timeout)
