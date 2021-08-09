# -*- coding: utf-8 -*-
"""
事件触发器：提供更多处理事件的方式。
"""
import asyncio
from typing import (
    Any, Awaitable, Callable, Generic, Optional, Type, TypeVar, Union
)

from mirai.utils import async_

TEvent = TypeVar('TEvent')


class Trigger(Generic[TEvent]):
    """
    事件触发器。
    """
    event_name: Type[TEvent]
    filter: Optional[Callable[[TEvent], Union[Awaitable[Any], Any]]]
    priority: int
    _future: Optional[asyncio.Future]
    _waited: bool

    def __init__(
        self,
        event_name: Type[TEvent],
        priority: int = 0,
        filter: Optional[Callable[[TEvent], Union[Awaitable[Any], Any]]] = None
    ):
        self.event_name = event_name
        self.priority = priority
        self.filter = filter
        self._future = None
        self._waited = False

    def __del__(self):
        self._future.cancel()

    def set_filter(
        self, filter: Callable[[TEvent], Union[Awaitable[Any], Any]]
    ):
        self.filter = filter
        return filter

    def __call__(
        self,
        filter: Optional[Callable[[TEvent], Union[Awaitable[Any],
                                                  Any]]] = None,
        **kwargs
    ):
        if filter is not None:
            self.set_filter(filter)
            return self
        else:
            return self.wait(**kwargs)

    async def catch(self, event: TEvent) -> bool:
        """尝试捕获一个事件。"""
        if self._future is None or self._future.done():
            return False
        if self.filter is not None:
            try:
                result = await async_(self.filter(event))
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
        return self._waited or bool(self._future and self._future.done())

    def add_done_callback(self, callback: Callable[[asyncio.Future], Any]):
        """添加回调。"""
        if self._future:
            self._future.add_done_callback(callback)

    def reset(self) -> 'Trigger[TEvent]':
        """重置事件触发器。"""
        if self._future:
            self._future.cancel()
        self._future = asyncio.get_running_loop().create_future()
        self._waited = False
        return self

    async def wait(self, timeout: float = 0.):
        """等待事件触发。"""
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
