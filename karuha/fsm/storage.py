import logging
from abc import ABC, ABCMeta, abstractmethod
from collections import defaultdict
from copy import copy
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict, Optional, Type, Union, overload

from .state import State, StatesGroup

# from karuha import Message


# from karuha.text.message import MessageSession


StateType = Union[str, None, State, StatesGroup, Type[StatesGroup]]


@dataclass(frozen=True)
class StorageKey:
    bot_name: str
    topic: str
    # user_id: Optional[int] = None

    @staticmethod
    def from_message(message) -> "StorageKey":
        return StorageKey(
            bot_name=message.bot.name,
            topic=message.topic,
            # user_id=message.user_id,
        )

    @staticmethod
    def from_session(session) -> "StorageKey":
        return StorageKey(
            bot_name=session.bot.name,
            topic=session.topic,
        )


class StorageMeta(ABCMeta):
    _instance = None

    def __call__(cls, *args, **kwargs) -> "BaseStorage":
        if StorageMeta._instance is not None and StorageMeta._instance.__class__ != cls:
            logging.warning(
                f"Trying to create instance of {cls.__name__} but singleton instance of {StorageMeta._instance.__class__.__name__} already exists"
            )
        if StorageMeta._instance is None:
            StorageMeta._instance = super(StorageMeta, cls).__call__(*args, **kwargs)
            logging.debug(f"Created new storage instance with class {cls.__name__}")
        return StorageMeta._instance


class BaseStorage(ABC, metaclass=StorageMeta):
    """Base class for FSM storages"""

    @abstractmethod
    async def set_state(self, key: StorageKey, state: StateType) -> None:
        """Set the state for a given key"""

    @abstractmethod
    async def get_state(self, key: StorageKey) -> StateType:
        """Get the state for a given key"""

    @abstractmethod
    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        """Set the data for a given key"""

    @abstractmethod
    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        """Get the data for a given key"""

    @overload
    async def get_value(
        self, storage_key: StorageKey, dict_key: str
    ) -> Optional[Any]: ...

    @overload
    async def get_value(
        self, storage_key: StorageKey, dict_key: str, default: Any
    ) -> Any: ...

    async def get_value(
        self, storage_key: StorageKey, dict_key: str, default: Optional[Any] = None
    ) -> Optional[Any]:
        """Get the value for a given key"""
        data = self.storage[storage_key].data
        return copy(data.get(dict_key, default))

    async def update_data(
        self, key: StorageKey, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update date in the storage for key (like dict.update)

        :param key: storage key
        :param data: partial data
        :return: new data
        """
        current_data = await self.get_data(key=key)
        current_data.update(data)
        await self.set_data(key=key, data=current_data)
        return current_data.copy()

    @abstractmethod
    async def close(self) -> None:  # pragma: no cover
        """Close storage (database connection, file or etc.)"""
        pass


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


def get_storage() -> BaseStorage:
    """Get current storage instance or create new one"""
    if StorageMeta._instance is None:
        print("creating new storage")
        StorageMeta._instance = MemoryStorage()
    return StorageMeta._instance
