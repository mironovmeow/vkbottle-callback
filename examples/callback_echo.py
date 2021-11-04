"""
Очень простой пример.
При сообщение отправляет текст пользователя и callback кнопку с его текстом.
При нажатии на кнопку, появляется snackbar c этим же текстом.
"""
import sys

from vkbottle import Bot, Callback, Keyboard
from vkbottle.bot import Message

from vkbottle_callback import MessageEvent, MessageEventLabeler

bot = Bot(
    token=sys.argv[-1],
    labeler=MessageEventLabeler()
)


@bot.on.message()
async def message_handler(message: Message):
    keyboard = (
        Keyboard(inline=True)
            .add(Callback(message.text, {"text": message.text}))
            .get_json()
    )
    await message.answer(message.text, keyboard=keyboard)


@bot.on.message_event()
async def event_handler(event: MessageEvent):
    await event.show_snackbar(
        event.get_payload_json().get("text", "Не найдено...")
    )


bot.run_forever()
