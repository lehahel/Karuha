import json
from typing import Any, Callable, Dict, Optional, cast
from karuha.fsm.state import State
from karuha.fsm.storage import StorageKey
from .base import BaseStorage, DefaultKeyBuilder, KeyBuilder, StateType

from redis.asyncio.client import Redis
from redis.typing import ExpiryT


class RedisStorage(BaseStorage):
    def __init__(
        self,
        redis: Redis,
        key_builder: Optional[KeyBuilder] = None,
        state_ttl: Optional[ExpiryT] = None,
        data_ttl: Optional[ExpiryT] = None,
        json_loads: Callable[..., Any] = json.loads,
        json_dumps: Callable[..., str] = json.dumps,
    ):
        self.redis = redis
        self.key_builder = key_builder or DefaultKeyBuilder()
        self.state_ttl = state_ttl
        self.data_ttl = data_ttl
        self.json_loads = json_loads
        self.json_dumps = json_dumps


    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        key = self.key_builder.build(key=key, part="state")
        if state is None:
            await self.redis.delete(key)
        else:
            await self.redis.set(
                name=key,
                value=cast(str, state.state if isinstance(state, State) else state),
                ex=self.state_ttl,
            )

    async def get_state(self, key: StorageKey) -> Optional[str]:
        key = self.key_builder.build(key=key, part="state")
        value = await self.redis.get(key)
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return cast(Optional[str], value)

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        key = self.key_builder.build(key=key, part="data")
        if not data:
            await self.redis.delete(key)
        else:
            await self.redis.set(
                name=key,
                value=self.json_dumps(data),
                ex=self.data_ttl,
            )

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        key = self.key_builder.build(key=key, part="data")
        value = await self.redis.get(key)
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return cast(Dict[str, Any], self.json_loads(value))

    async def close(self) -> None:
        await self.redis.aclose(close_connection_pool=True)
