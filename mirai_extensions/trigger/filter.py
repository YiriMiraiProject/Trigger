# -*- coding: utf-8 -*-

from typing import (
    Any, Callable, Generic, Iterable, List, Optional, Type, TypeVar
)

TEvent = TypeVar('TEvent')

TFilter = Callable[[TEvent], Optional[Any]]


class BaseFilter(Generic[TEvent]):
    """事件过滤器，提供对事件进行选择性过滤和解析的功能。

    事件过滤器提供了 mixin 机制，允许混入其他过滤器。

    过滤器会先检查混入的过滤器，若任何一个未捕获，直接停止捕获，返回“未捕获”状态。
    """
    mixin: List['BaseFilter[TEvent]']
    """过滤器混入。"""

    def __init__(self, mixin: Iterable['BaseFilter[TEvent]']):
        """
        Args:
            mixin: 过滤器混入。
                过滤器会先检查混入的过滤器，若任何一个未捕获，直接停止捕获，返回“未捕获”状态。
        """
        self.mixin = list(mixin)

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.mixin = []
        return instance

    def _catch(self, event: TEvent) -> Optional[Any]:
        """`catch` 的内部实现，不包括 mixin。"""
        return event

    def catch(self, event: TEvent) -> Optional[Any]:
        """尝试捕获并解析一个事件。

        Args:
            event: 事件。

        Returns:
            Any: 解析后的结果。
            None: 未捕获。
        """
        if any(filter.catch(event) is None for filter in self.mixin):
            return None
        return self._catch(event)


class Filter(BaseFilter[TEvent]):
    """事件过滤器，允许用户传入自定义的捕获函数。

    捕获函数可以在创建过滤器时设置，或者通过装饰器的方式设置。

    ```python
    # 方式一
    def filter_one_func(event: FriendMessage):
        if event.sender.id == 12345678:
            return event.sender.nickname or ''
    filter_one = Filter(FriendMessage, func=filter_one_func)

    # 方式二
    @Filter(FriendMessage)
    def filter_two(event: FriendMessage):
        if event.sender.id == 12345678:
            return event.sender.nickname or ''
    ```

    当使用类装饰器的方式创建过滤器时，被装饰函数的名称将失效。比如上例中，`filter_two` 将不再是函数，
    而是成为 Filter 实例。

    上例中的过滤器将检测好友消息的发送对象，只有来自 12345678 的消息会被捕获。其他情况下，过滤器返回默认值 None，
    不会被捕获。
    """
    event_name: Type[TEvent]
    """过滤器捕获的事件类型。"""

    def __init__(
        self,
        event_name: Type[TEvent],
        mixin: Optional[Iterable[BaseFilter[TEvent]]] = None,
        func: Optional[TFilter[TEvent]] = None
    ):
        """
        Args:
            event_name: 过滤器捕获的事件类型。
            mixin: 过滤器混入。
                过滤器会先检查混入的过滤器，若任何一个未捕获，直接停止捕获，返回“未捕获”状态。
            func: 自定义的捕获函数。
        """
        super().__init__(mixin or [])
        self.event_name = event_name
        self._func: Optional[TFilter[TEvent]] = func

    def __call__(self, func: TFilter[TEvent]):
        self._func = func
        return self

    def _catch(self, event: TEvent) -> Optional[Any]:
        if self._func is None:
            return event
        return self._func(event)
