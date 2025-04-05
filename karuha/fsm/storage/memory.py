from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict

from karuha.fsm.storage.base import StateType, StorageKey

from .base import BaseStorage


@dataclass
class MemoryStorageRecord:
    data: Dict[str, Any] = field(default_factory=dict)
    state: StateType = None


class MemoryStorage(BaseStorage):
    """Memory storage for FSM"""

    def __init__(self):
        self.storage: DefaultDict[StorageKey, MemoryStorageRecord] = defaultdict(
            MemoryStorageRecord
        )

    async def set_state(self, key: StorageKey, state: StateType) -> None:
        """Set the state for a given key"""
        self.storage[key].state = state

    async def get_state(self, key: StorageKey) -> StateType:
        """Get the state for a given key"""
        return self.storage[key].state

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        """Set the data for a given key"""
        self.storage[key].data = data

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        """Get the data for a given key"""
        return self.storage[key].data

    async def close(self) -> None:  # pragma: no cover
        """Close storage (database connection, file or etc.)"""
        pass
