"""
В библиотеке есть поддержка рулзов из vkbottle, которые взаимодействуют с:
1) peer_id: PeerRule, FromPeerRule
2) payload: PayloadRule, PayloadContainsRule, PayloadMapRule
3) state_dispenser: StateRule
И прочие рулзы (FuncRule, CoroutineRule).

Все они находятся в vkbottle_callback.rules. Их короткие версии добавлены в MessageEventLabeler.

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
        .add(Callback(message.text, {"type": "text", "text": message.text}))
        .add(Callback("Payload", {
            "int": 42,
            "str": "42",
            "float": 4.2,
            "dict": {"42": 42},
            "list": ["42", 42],
        }))
        .get_json()
    )
    await message.answer(message.text, keyboard=keyboard)


@bot.on.message_event(blocking=False, from_chat=True)
async def event_handler(event: MessageEvent):
    await event.send_message("Я в беседе почему-то сижу... А хочу в личных сообщениях")


@bot.on.message_event(payload={"type": "text", "text": "привет"})
async def event_handler(event: MessageEvent):
    await event.show_snackbar(
        "Нет, не привет!"
    )


@bot.on.message_event(payload_contains={"type": "text"})
async def first_event_handler(event: MessageEvent):
    await event.show_snackbar(
        event.get_payload_json()["text"]
    )


@bot.on.message_event(payload_map={"int": int, "str": str, "float": float, "dict": dict, "list": list})
async def second_event_handler(event: MessageEvent):
    await event.show_snackbar(
        "PayloadMapRule успешно работает"
    )


bot.run_forever()
