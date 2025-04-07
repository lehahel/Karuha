import json
from typing import Any, Callable, Dict, Optional, cast
from karuha.fsm.state import State
from karuha.fsm.storage import StorageKey
from .base import BaseStorage, DefaultKeyBuilder, KeyBuilder, StateType

import asyncpg


class PostgresStorage(BaseStorage):
    def __init__(
        self,
        pool: asyncpg.Pool,
        key_builder: Optional[KeyBuilder] = None,
        state_table: str = "fsm_state",
        data_table: str = "fsm_data",
        json_loads: Callable[..., Any] = json.loads,
        json_dumps: Callable[..., str] = json.dumps,
    ):
        self.pool = pool
        self.key_builder = key_builder or DefaultKeyBuilder()
        self.state_table = state_table
        self.data_table = data_table
        self.json_loads = json_loads
        self.json_dumps = json_dumps

    @classmethod
    async def from_connection_string(
        cls,
        dsn: str,
        *,
        key_builder: Optional[KeyBuilder] = None,
        state_table: str = "fsm_state",
        data_table: str = "fsm_data",
        json_loads: Callable[..., Any] = json.loads,
        json_dumps: Callable[..., str] = json.dumps,
        **pool_kwargs: Any,
    ) -> "PostgresStorage":
        """Create PostgresStorage instance from connection string."""
        pool = await asyncpg.create_pool(dsn, **pool_kwargs)
        return cls(
            pool=pool,
            key_builder=key_builder,
            state_table=state_table,
            data_table=data_table,
            json_loads=json_loads,
            json_dumps=json_dumps,
        )

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        key_str = self.key_builder.build(key=key, part="state")
        async with self.pool.acquire() as conn:
            if state is None:
                await conn.execute(
                    f"DELETE FROM {self.state_table} WHERE key = $1",
                    key_str
                )
            else:
                state_str = state.state if isinstance(state, State) else state
                await conn.execute(
                    f"""
                    INSERT INTO {self.state_table} (key, state)
                    VALUES ($1, $2)
                    ON CONFLICT (key) DO UPDATE SET state = $2
                    """,
                    key_str,
                    cast(str, state_str)
                )

    async def get_state(self, key: StorageKey) -> Optional[str]:
        key_str = self.key_builder.build(key=key, part="state")
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT state FROM {self.state_table} WHERE key = $1",
                key_str
            )
            return row['state'] if row else None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        key_str = self.key_builder.build(key=key, part="data")
        async with self.pool.acquire() as conn:
            if not data:
                await conn.execute(
                    f"DELETE FROM {self.data_table} WHERE key = $1",
                    key_str
                )
            else:
                await conn.execute(
                    f"""
                    INSERT INTO {self.data_table} (key, data)
                    VALUES ($1, $2)
                    ON CONFLICT (key) DO UPDATE SET data = $2
                    """,
                    key_str,
                    self.json_dumps(data)
                )

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        key_str = self.key_builder.build(key=key, part="data")
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT data FROM {self.data_table} WHERE key = $1",
                key_str
            )
            if row and row['data']:
                return cast(Dict[str, Any], self.json_loads(row['data']))
            return {}

    async def close(self) -> None:
        await self.pool.close()

