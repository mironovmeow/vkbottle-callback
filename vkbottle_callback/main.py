from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union

from vkbottle import ABCView, BaseReturnManager
from vkbottle.dispatch.handlers import FromFuncHandler
from vkbottle.framework.bot import BotLabeler
from vkbottle.modules import logger
from vkbottle_types.events import MessageEvent as _MessageEvent

from vkbottle_callback.rules import *
from vkbottle_callback.types import MessageEvent

if TYPE_CHECKING:
    from vkbottle import ABCAPI, ABCStateDispenser
    from vkbottle.dispatch.rules import ABCRule
    from vkbottle.dispatch.views import ABCView
    from vkbottle.dispatch.views.bot import ABCBotMessageView, RawBotEventView

    from vkbottle.framework.bot.labeler.abc import LabeledMessageHandler


class MessageEventReturnHandler(BaseReturnManager):
    @BaseReturnManager.instance_of(str)
    async def str_handler(self, value: str, event: MessageEvent, _: dict):
        await event.show_snackbar(value)


def message_event_min(event: dict, ctx_api: "ABCAPI") -> "MessageEvent":
    update = _MessageEvent(**event)
    message_event = MessageEvent(
        **update.object.dict(),
        group_id=update.group_id,
    )
    setattr(message_event, "unprepared_ctx_api", ctx_api)
    return message_event


class MessageEventView(ABCView):
    def __init__(self):
        super().__init__()
        self.handler_return_manager = MessageEventReturnHandler()

    async def process_event(self, event: dict) -> bool:
        return event["type"] == "message_event"

    async def handle_event(
            self, event: dict, ctx_api: "ABCAPI", state_dispenser: "ABCStateDispenser"
    ) -> None:

        logger.debug("Handling event ({}) with message_event view".format(event.get("event_id")))
        context_variables: dict = {}
        message_event = message_event_min(event, ctx_api)
        message_event.state_peer = await state_dispenser.cast(message_event.peer_id)

        mw_instances = await self.pre_middleware(message_event, context_variables)  # type: ignore
        if mw_instances is None:
            logger.info("Handling stopped, pre_middleware returned error")
            return

        handle_responses = []
        handlers = []

        for handler in self.handlers:
            result = await handler.filter(message_event)  # type: ignore
            logger.debug("Handler {} returned {}".format(handler, result))

            if result is False:
                continue

            elif isinstance(result, dict):
                context_variables.update(result)

            handler_response = await handler.handle(message_event, **context_variables)  # type: ignore
            handle_responses.append(handler_response)
            handlers.append(handler)

            return_handler = self.handler_return_manager.get_handler(handler_response)
            if return_handler is not None:
                await return_handler(
                    self.handler_return_manager, handler_response, message_event, context_variables
                )

            if handler.blocking:
                break

        await self.post_middleware(mw_instances, handle_responses, handlers)


LabeledMessageEventHandler = Callable[..., Callable[[MessageEvent], Any]]
DEFAULT_CUSTOM_RULES: Dict[str, Type[ABCMessageEventRule]] = {
    "from_chat": PeerRule,
    "peer_ids": FromPeerRule,
    "payload": PayloadRule,
    "payload_contains": PayloadContainsRule,
    "payload_map": PayloadMapRule,
    "func": FuncRule,
    "coro": CoroutineRule,
    "coroutine": CoroutineRule,
    "state": StateRule
}


class MessageEventLabeler(BotLabeler):
    def __init__(
            self,
            message_view: Optional["ABCBotMessageView"] = None,
            raw_event_view: Optional["RawBotEventView"] = None,
            custom_rules: Optional[Dict[str, Type["ABCRule"]]] = None,
            auto_rules: Optional[List["ABCRule"]] = None,
            message_event_view: Optional["MessageEventView"] = None
    ):
        super().__init__(message_view, raw_event_view, custom_rules, auto_rules)
        self.custom_rules = custom_rules or DEFAULT_CUSTOM_RULES
        self.message_event_view = message_event_view or MessageEventView()

    def message_event(
        self, *rules: "ABCRule", blocking: bool = True, **custom_rules
    ) -> "LabeledMessageHandler":
        def decorator(func):
            self.message_event_view.handlers.append(
                FromFuncHandler(
                    func,
                    *rules,
                    *self.auto_rules,
                    *self.get_custom_rules(custom_rules),
                    blocking=blocking,
                )
            )
            return func

        return decorator

    def load(self, labeler: Union[BotLabeler, "MessageEventLabeler"]):
        if type(labeler) is MessageEventLabeler:
            self.message_event_view.handlers.extend(labeler.message_event_view.handlers)
            self.message_event_view.middlewares.update(labeler.message_event_view.middlewares)

        self.message_view.handlers.extend(labeler.message_view.handlers)
        self.message_view.middlewares.update(labeler.message_view.middlewares)
        for event, handler_basements in labeler.raw_event_view.handlers.items():
            event_handlers = self.raw_event_view.handlers.get(event)
            if event_handlers:
                event_handlers.extend(handler_basements)
            else:
                self.raw_event_view.handlers[event] = handler_basements
        self.raw_event_view.middlewares.update(labeler.raw_event_view.middlewares)

    def views(self) -> Dict[str, "ABCView"]:
        return {
            "message": self.message_view,
            "message_event": self.message_event_view,
            "raw": self.raw_event_view
        }


__all__ = (
    "MessageEventView",
    "MessageEventLabeler"
)
