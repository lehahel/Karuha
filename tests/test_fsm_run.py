from pydantic_core import from_json

from karuha import on_command
from karuha.fsm.context import FSMContext
from karuha.fsm.rule import on_state
from karuha.fsm.state import State, StatesGroup
from karuha.fsm.storage.base import StorageKey
from karuha.text.message import MessageSession
from tests.utils import AsyncBotTestCase


class TestBotState(StatesGroup):
    state1 = State()
    state2 = State()


@on_command("start")
async def on_start(session: MessageSession) -> None:
    fsm_context = FSMContext.from_session(session)
    await fsm_context.set_state(TestBotState.state1)
    await session.send("started")


@on_state(TestBotState.state1)
async def on_state1(session: MessageSession, text: str) -> None:
    fsm_context = FSMContext.from_session(session)
    await fsm_context.set_state(TestBotState.state2)
    await fsm_context.set_data({"text": text})
    await session.send("state1")


@on_state(TestBotState.state2)
async def on_state2(session: MessageSession, text: str) -> None:
    fsm_context = FSMContext.from_session(session)
    await fsm_context.clear()
    await session.send("state2")


class TestFSMOnState(AsyncBotTestCase):
    async def test_on_state(self) -> None:
        await self.put_bot_content(b'{"txt": "/start"}')
        pub_msg = await self.get_bot_pub()
        self.assertEqual(from_json(pub_msg.content), "started")

        fsm_context = FSMContext(
            StorageKey(
                bot_name=self.bot.name,
                topic=pub_msg.topic,
            )
        )

        state = await fsm_context.get_state()
        data = await fsm_context.get_data()
        value = await fsm_context.get_value("text")
        self.assertEqual(state, TestBotState.state1)
        self.assertEqual(data, {})
        self.assertEqual(value, None)

        await self.put_bot_content(b'{"txt": "some_text"}')
        pub_msg = await self.get_bot_pub()
        self.assertEqual(from_json(pub_msg.content), "state1")

        state = await fsm_context.get_state()
        data = await fsm_context.get_data()
        value = await fsm_context.get_value("text")
        self.assertEqual(state, TestBotState.state2)
        self.assertEqual(data, {"text": "some_text"})
        self.assertEqual(value, "some_text")

        await self.put_bot_content(b'{"txt": "absolutely random text"}')
        pub_msg = await self.get_bot_pub()
        self.assertEqual(from_json(pub_msg.content), "state2")

        state = await fsm_context.get_state()
        data = await fsm_context.get_data()
        value = await fsm_context.get_value("text")
        self.assertEqual(state, None)
        self.assertEqual(data, {})
        self.assertEqual(value, None)
