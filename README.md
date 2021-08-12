# Trigger

> 此项目隶属于 [YiriMirai](https://github.com/YiriMiraiProject/YiriMirai) 的拓展模块。

事件触发器：提供更多处理事件的方式。

目前已经实现的有两种：中断控制器和事件接收控制器。

## 安装

```shell
pip install yiri-mirai-trigger
# 或者使用 poetry
poetry add yiri-mirai-trigger
```

## 使用

### 中断控制器

```python
from mirai_extensions.trigger import Trigger, InterruptControl

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

### 事件接收控制器

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

更多信息，请参考[文档](https://yiri-mirai.vercel.app/docs/extensions/trigger)或 [API 文档](https://yirimiraiproject.github.io/Trigger)。

## 开源协议

本项目采用 AGPL-3.0 协议。

请注意，AGPL-3.0 是传染性协议。如果你的项目引用了本项目，请在发布时公开源代码，并同样采用 AGPL-3.0 协议。
