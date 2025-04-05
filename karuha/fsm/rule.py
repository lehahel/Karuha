from typing import Type

from karuha import Message
from karuha.command import BaseRule
from karuha.command.decoractor import on_rule

from .storage.base import StateType


class FSMRule(BaseRule):
    def __init__(self, state: Type[StateType]) -> None:
        self._target_state = state

    def match(self, message: Message, /, **kwargs) -> float:
        current_state = kwargs.get("fsm_state", None)
        if current_state is None:
            return 0.0

        return 1.0 if current_state == self._target_state else 0.0


def on_state(state: Type[StateType]):
    return on_rule(FSMRule(state))
