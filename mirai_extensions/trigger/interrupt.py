# -*- coding: utf-8 -*-
"""
本模块提供中断控制器相关。
"""
import logging
from typing import Any, Dict

from mirai.bus import AbstractEventBus
from mirai.utils import PriorityDict
from mirai_extensions.trigger.trigger import Trigger

logger = logging.getLogger(__name__.replace('mirai_extensions', 'mirai'))


class InterruptControl:
    """中断控制器，用于实现在一个消息处理器中间监听另一个消息事件。

    使用 Trigger 定义触发器，接下来使用 `inc.wait` 等待触发器。

    ```python
    inc = InterruptControl(bot)

    @bot.on(FriendMessage)
    async def on_friend_message(event: FriendMessage):
        if str(event.message_chain).strip() == '你是谁':
            await bot.send(event, '我是 Yiri。你呢？')

            @Trigger(FriendMessage)
            async def trigger(event_new: FriendMessage):
                if event.sender.id == event_new.sender.id:
                    msg = str(event.message_chain)
                    if msg.startswith('我是'):
                        return msg[2:]

            name = await inc.wait(trigger, timeout=60.)
            if name:
                await bot.send(event, f'你好，{name}。')
    ```

    `inc.wait` 的返回值为触发器中过滤器的返回值，或者当达到超时后，返回 `None`。
    """
    def __init__(self, bus: AbstractEventBus, priority: int = 15):
        """
        Args:
            bus (`AbstractEventBus`): 事件总线。
            priority (`int`): 中断控制器工作的优先级，默认值 15。
        """
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
        """监听一个触发器，等待其完成。

        Args:
            trigger (`Trigger`): 触发器。
            timeout (`float`): 超时时间，单位为秒。

        Returns:
            `Any`: 触发器的结果。
            `None`: 触发器超时。
        """
        event_name = trigger.event_name

        if event_name not in self._triggers:
            self._triggers[event_name] = PriorityDict()
            self._new_handler(event_name)

        self._triggers[event_name].add(trigger.priority, trigger)

        @trigger.add_done_callback
        def _(_: Trigger):
            self._triggers[event_name].remove(trigger)

        logger.debug(f'[InterruptControl] 等待触发器 {trigger}。')
        return await trigger.wait(timeout)
