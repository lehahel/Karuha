from typing import Any, Dict, Optional, overload

from .storage import get_storage
from .storage.base import StateType, StorageKey


class FSMContext:
    def __init__(self, key: StorageKey) -> None:
        self._storage = get_storage()
        self.key = key

    @staticmethod
    def from_message(message) -> "FSMContext":
        return FSMContext(StorageKey.from_message(message))

    @staticmethod
    def from_session(session) -> "FSMContext":
        return FSMContext(StorageKey.from_session(session))

    async def set_state(self, state: StateType = None) -> None:
        return await self._storage.set_state(self.key, state)

    async def get_state(self) -> StateType:
        return await self._storage.get_state(self.key)

    async def set_data(self, data: Dict[str, Any]) -> None:
        return await self._storage.set_data(self.key, data)

    async def get_data(self) -> Dict[str, Any]:
        return await self._storage.get_data(self.key)

    @overload
    async def get_value(self, key: str) -> Optional[Any]: ...

    @overload
    async def get_value(self, key: str, default: Any) -> Any: ...

    async def get_value(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        return await self._storage.get_value(self.key, key, default)

    async def update_data(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self._storage.update_data(self.key, data=kwargs)

    async def clear(self) -> None:
        await self.set_state(None)
        await self.set_data({})
