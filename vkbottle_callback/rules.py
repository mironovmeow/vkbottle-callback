import inspect
import types
from abc import abstractmethod
from typing import Any, Awaitable, Callable, Coroutine, Dict, List, Tuple, Union

from vkbottle import ABCRule
from vkbottle.tools.validator import (
    ABCValidator,
    CallableValidator,
    EqualsValidator,
    IsInstanceValidator,
)
from vkbottle_types import BaseStateGroup

from vkbottle_callback import MessageEvent

PayloadMap = List[Tuple[str, Union[type, Callable[[Any], bool], ABCValidator, Any]]]
PayloadMapStrict = List[Tuple[str, ABCValidator]]
PayloadMapDict = Dict[str, Union[dict, type]]


class ABCMessageEventRule(ABCRule):
    @abstractmethod
    async def check(self, event: MessageEvent) -> bool:
        pass


class PeerRule(ABCMessageEventRule):
    def __init__(self, from_chat: bool = True):
        self.from_chat = from_chat

    async def check(self, event: MessageEvent) -> bool:
        return self.from_chat is (event.peer_id != event.user_id)


class FromPeerRule(ABCMessageEventRule):
    def __init__(self, peer_ids: Union[List[int], int]):
        if isinstance(peer_ids, int):
            peer_ids = [peer_ids]
        self.peer_ids = peer_ids

    async def check(self, event: MessageEvent) -> bool:
        return event.peer_id in self.peer_ids


class PayloadRule(ABCMessageEventRule):
    def __init__(self, payload: Union[dict, List[dict]]):
        if isinstance(payload, dict):
            payload = [payload]
        self.payload = payload

    async def check(self, event: MessageEvent) -> bool:
        return event.get_payload_json() in self.payload


class PayloadContainsRule(ABCMessageEventRule):
    def __init__(self, payload_particular_part: dict):
        self.payload_particular_part = payload_particular_part

    async def check(self, event: MessageEvent) -> bool:
        payload = event.get_payload_json(unpack_failure=lambda p: {})
        for k, v in self.payload_particular_part.items():
            if payload.get(k) != v:
                return False
        return True


class PayloadMapRule(ABCMessageEventRule):
    def __init__(self, payload_map: Union[PayloadMap, PayloadMapDict]):
        if isinstance(payload_map, dict):
            payload_map = self.transform_to_map(payload_map)
        self.payload_map = self.transform_to_callbacks(payload_map)

    @classmethod
    def transform_to_map(cls, payload_map_dict: PayloadMapDict) -> PayloadMap:
        """ Transforms PayloadMapDict to PayloadMap """
        payload_map = []
        for (k, v) in payload_map_dict.items():
            if isinstance(v, dict):
                v = cls.transform_to_map(v)  # type: ignore
            payload_map.append((k, v))
        return payload_map  # type: ignore

    @classmethod
    def transform_to_callbacks(cls, payload_map: PayloadMap) -> PayloadMapStrict:
        """ Transforms PayloadMap to PayloadMapStrict """
        for i, (key, value) in enumerate(payload_map):
            if isinstance(value, type):
                value = IsInstanceValidator(value)
            elif isinstance(value, list):
                value = cls.transform_to_callbacks(value)
            elif isinstance(value, types.FunctionType):
                value = CallableValidator(value)
            elif not isinstance(value, ABCValidator):
                value = EqualsValidator(value)
            payload_map[i] = (key, value)
        return payload_map  # type: ignore

    @classmethod
    async def match(cls, payload: dict, payload_map: PayloadMapStrict):
        """ Matches payload with payload_map recursively """
        for (k, validator) in payload_map:
            if k not in payload:
                return False
            elif isinstance(validator, list):
                if not isinstance(payload[k], dict):
                    return False
                elif not await cls.match(payload[k], validator):
                    return False
            elif not await validator.check(payload[k]):
                return False
        return True

    async def check(self, event: MessageEvent) -> bool:
        payload = event.get_payload_json(unpack_failure=lambda p: {})
        return await self.match(payload, self.payload_map)


class FuncRule(ABCMessageEventRule):
    def __init__(self, func: Union[Callable[[MessageEvent], Union[bool, Awaitable]]]):
        self.func = func

    async def check(self, event: MessageEvent) -> Union[dict, bool]:
        if inspect.iscoroutinefunction(self.func):
            return await self.func(event)  # type: ignore
        return self.func(event)  # type: ignore


class CoroutineRule(ABCMessageEventRule):
    def __init__(self, coroutine: Coroutine):
        self.coroutine = coroutine

    async def check(self, message: MessageEvent) -> Union[dict, bool]:
        return await self.coroutine


class StateRule(ABCMessageEventRule):
    def __init__(self, state: Union[List[BaseStateGroup], BaseStateGroup]):
        if not isinstance(state, list):
            state = [] if state is None else [state]
        self.state = state

    async def check(self, event: MessageEvent) -> bool:
        if event.state_peer is None:
            return not self.state
        return event.state_peer.state in self.state


__all__ = (
    "ABCMessageEventRule",
    "PeerRule",
    "FromPeerRule",
    "PayloadRule",
    "PayloadContainsRule",
    "PayloadMapRule",
    "FuncRule",
    "CoroutineRule",
    "StateRule"
)
