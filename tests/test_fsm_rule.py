from unittest import TestCase

from karuha.fsm.rule import FSMRule
from karuha.fsm.state import State, StatesGroup


class TestBotState(StatesGroup):
    state1 = State()
    state2 = State()


class BadState(StatesGroup):
    state1 = State()
    invalid_state = State()


class TestFSMRule(TestCase):
    def test_fsm_rule_match(self) -> None:
        # Create new rule
        rule1 = FSMRule(TestBotState.state1)

        # Test rule match
        self.assertEqual(rule1.match("some text", fsm_state=TestBotState.state1), 1.0)
        self.assertEqual(rule1.match("some text", fsm_state=TestBotState.state2), 0.0)
        self.assertEqual(rule1.match("some text", fsm_state=None), 0.0)
        self.assertEqual(rule1.match("some text", fsm_state=BadState.state1), 0.0)
        self.assertEqual(
            rule1.match("some text", fsm_state=BadState.invalid_state), 0.0
        )
