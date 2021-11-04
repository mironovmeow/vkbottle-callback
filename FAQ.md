# FAQ (Часто Задаваемые Вопросы)

### Почему на строчке `@bot.on.message_event()` (или `@bp.on.message_event()`) у меня предупреждение?

Что такое `*.on`? Это довольно простая функция:

```python
@property
def on(self) -> "BotLabeler":
    return self.labeler
```

Прошу заметить, что код всё равно **работает**. Но из-за type hint, type-checker'ы не понимают, что за
метод `.message_event()`, поскольку его нет в `BotLabeler`. Есть несколько способов решения проблемы:

1) Добавить в исключение IDE. В PyCharm: `ALT+ENTER` на ошибке, `ignore an unresolved reference`
2) `*.on.message_event()  # type: ignore`. Тогда type-checker не будет обращать внимания на типы.
3) Вместо `*.on` использовать сам `labeler`. Тогда код будет вот таким:

```python
from vkbottle import Bot
from vkbottle_callback import MessageEventLabeler, MessageEvent

labeler = MessageEventLabeler()

bot = Bot(token=..., labeler=MessageEventLabeler())


@labeler.message_event()
async def handler(event: MessageEvent):
    ...
```

## Остался вопрос?

Лучше всего написать мне [лично](https://vk.me/mironovmeow/). Сразу смогу помочь и ответить на вопрос.
