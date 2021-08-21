# -*- coding: utf-8 -*-
"""
此模块提供事件触发器相关。
"""
import asyncio
from typing import Any, Callable, Generic, Optional, Type, TypeVar

from mirai_extensions.trigger.filter import Filter

TEvent = TypeVar('TEvent')


class Trigger(Generic[TEvent]):
    """事件触发器，提供等待符合特定条件的事件的功能。

    事件触发器类似于 asyncio.Future，有已完成和未完成两种状态。和 Future 一样，Trigger 也是低层级 API。
    大多数情况下，你不需要用到 Trigger 的实现，而是通过中断控制器、事件接收控制器来使用 Trigger。

    触发器创建后，默认为未完成状态。通过 catch 方法尝试捕获事件，捕获成功后将进入已完成状态。
    使用 wait 方法等待一个触发器，直到触发器完成。

    触发器内部的逻辑由过滤器（`mirai_extensions.trigger.filter.Filter`）实现。在创建触发器时，指定使用的过滤器。

    事件被捕获后，触发器将进入已完成状态，同时触发器的结果会被设置为过滤器的返回值，在上例中就是好友的昵称。

    触发器的状态可以通过 done 方法来查询。

    使用 wait 方法等待触发器完成，并获得触发器的结果。

    ```python
    @Filter(FriendMessage)
    def filter(event: FriendMessage):
        if event.sender.id == 12345678:
            return event.sender.nickname or ''

    trigger = Trigger(filter)
    result = await trigger.wait()
    ```

    `wait` 方法有一个可选的 `timeout` 参数，表示等待的限时，如果超时则返回 None。

    使用 `catch` 方法尝试捕获事件。事件捕获成功后，触发器会进入已完成状态。
    """
    filter: Filter[TEvent]
    """过滤器。"""
    priority: int
    """优先级，小者优先。"""
    def __init__(
        self,
        filter: Filter[TEvent],
        priority: int = 0,
    ):
        """
        Args:
            filter: 过滤器。
            priority: 优先级，小者优先。
        """
        self.priority = priority
        self.filter = filter
        self._future: Optional[asyncio.Future] = None
        self._waited: bool = False

    def __del__(self):
        if self._future:
            self._future.cancel()

    @property
    def event_name(self) -> Type[TEvent]:
        """事件类型。"""
        return self.filter.event_name

    def catch(self, event: TEvent) -> bool:
        """尝试捕获一个事件。

        事件会传递给过滤器，过滤器返回一个非 None 的值，表示事件被捕获，
        事件触发器将把过滤器的返回值作为结果。

        事件捕获成功后，触发器会进入已完成状态。

        Args
            event: 事件。

        Returns:
            bool: 捕获成功与否。
        """
        if self._future is None or self.done():
            return False
        if self.filter is not None:
            try:
                result = self.filter.catch(event)
                if result is not None and not self._future.done():
                    self._future.set_result(result)
                    return True
            except Exception as e:
                if not self._future.done():
                    self._future.set_exception(e)
                    return True
        else:
            self._future.set_result(None)
            return True

        return False

    def done(self) -> bool:
        """触发器是否已经完成。"""
        return self._waited or bool(self._future and self._future.done())

    def add_done_callback(self, callback: Callable[['Trigger'], Any]):
        """添加触发器完成后的回调。

        回调函数接受唯一参数：触发器本身。

        Args:
            callback: 回调函数。
        """
        if self._future:
            self._future.add_done_callback(lambda _: callback(self))

    def reset(self) -> 'Trigger[TEvent]':
        """重置事件触发器。

        此方法将丢弃当前结果，并将触发器设置为未完成状态。

        注意，此方法必须被异步函数调用或间接调用。

        Returns:
            Trigger[TEvent]: 触发器本身。
        """
        if self._future:
            self._future.cancel()
        self._future = asyncio.get_running_loop().create_future()
        self._waited = False
        return self

    async def wait(self, timeout: float = 0.):
        """等待事件触发，返回事件触发器的结果。

        Args:
            timeout: 超时时间，单位为秒。

        Returns:
            Any: 触发器的结果。
            None: 触发器超时。
        """
        if self._waited:
            raise RuntimeError('触发器已被等待。')

        if self._future is None:
            self._future = asyncio.get_running_loop().create_future()

        try:
            if timeout > 0:
                return await asyncio.wait_for(self._future, timeout)
            else:
                return await self._future
        except asyncio.TimeoutError:
            return None
        finally:
            self._waited = self._future.done()
