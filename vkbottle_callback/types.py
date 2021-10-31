from typing import Any, List, Optional, Union
from warnings import warn

from vkbottle import ABCAPI, API
from vkbottle.modules import json
from vkbottle_types.events.objects.group_event_objects import MessageEventObject
from vkbottle_types.responses.messages import EditResponseModel, SendResponseModel


class MessageEvent(MessageEventObject):
    group_id: Optional[int] = None
    unprepared_ctx_api: Optional[Any] = None

    @property
    def ctx_api(self) -> Union["ABCAPI", "API"]:
        return getattr(self, "unprepared_ctx_api")

    @property
    def object(self) -> "MessageEvent":
        """
        Property for backward compatibility (event.object.user_id)
        :return: self
        """
        warn("Don't use \"object\" attribute for MessageEvent\n"
             "It's work without him", PendingDeprecationWarning)
        return self

    async def show_snackbar(self, text: str) -> int:
        return await self.ctx_api.messages.send_message_event_answer(
            event_id=self.event_id,
            user_id=self.user_id,
            peer_id=self.peer_id,
            event_data=json.dumps({
                "type": "show_snackbar",
                "text": text
            })
        )

    async def open_link(self, url: str) -> int:
        return await self.ctx_api.messages.send_message_event_answer(
            event_id=self.event_id,
            user_id=self.user_id,
            peer_id=self.peer_id,
            event_data=json.dumps({
                "type": "open_link",
                "link": url
            })
        )

    async def open_app(
            self,
            app_id: int,
            app_hash: str,
            owner_id: Optional[int] = None
    ) -> int:
        return await self.ctx_api.messages.send_message_event_answer(
            event_id=self.event_id,
            user_id=self.user_id,
            peer_id=self.peer_id,
            event_data=json.dumps({
                "type": "open_app",
                "app_id": app_id,
                "owner_id": owner_id,
                "hash": app_hash
            })
        )

    async def edit_message(
            self,
            message: Optional[str] = None,
            lat: Optional[float] = None,
            long: Optional[float] = None,
            attachment: Optional[str] = None,
            keep_forward_messages: Optional[bool] = None,
            keep_snippets: Optional[bool] = None,
            dont_parse_links: Optional[bool] = None,
            template: Optional[str] = None,
            keyboard: Optional[str] = None,
            **kwargs
    ) -> EditResponseModel:
        params = locals()
        params.pop("self")
        params.pop("kwargs")
        params.update(kwargs)
        params["peer_id"] = self.peer_id
        params["conversation_message_id"] = self.conversation_message_id
        print(params)
        return await self.ctx_api.messages.edit(
            **params
        )

    async def send_message(
            self,
            random_id: Optional[int] = None,
            message: Optional[str] = None,
            lat: Optional[float] = None,
            long: Optional[float] = None,
            attachment: Optional[str] = None,
            reply_to: Optional[int] = None,
            forward_messages: Optional[List[int]] = None,
            sticker_id: Optional[int] = None,
            keyboard: Optional[str] = None,
            payload: Optional[str] = None,
            dont_parse_links: Optional[bool] = None,
            disable_mentions: Optional[bool] = None,
            intent: Optional[str] = None,
            subscribe_id: Optional[int] = None,
            **kwargs
    ) -> SendResponseModel:
        params = locals()
        params.pop("self")
        params.pop("kwargs")
        params.update(kwargs)
        params["peer_id"] = self.peer_id
        return await self.ctx_api.messages.send(
            **params
        )


__all__ = (
    "MessageEvent"
)
