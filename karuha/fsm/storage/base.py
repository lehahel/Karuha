import logging
from abc import ABC, ABCMeta, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Type, Union, overload

from ..state import State, StatesGroup

DEFAULT_DESTINY = "default"

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


class KeyBuilder(ABC):
    """Base class for key builders"""

    @abstractmethod
    def build(
        self,
        key: StorageKey,
        part: Literal["state", "data"],
    ) -> str:
        """Build a key for a given storage part"""
        pass


class DefaultKeyBuilder(KeyBuilder):
    """Simple key builder with default prefix."""

    def __init__(
        self,
        *,
        prefix: str = "fsm",
        separator: str = ":",
        with_bot_id: bool = False,
        with_business_connection_id: bool = False,
        with_destiny: bool = False,
    ) -> None:
        self.prefix = prefix
        self.separator = separator
        self.with_bot_id = with_bot_id
        self.with_business_connection_id = with_business_connection_id
        self.with_destiny = with_destiny

    def build(
        self,
        key: StorageKey,
        part: Optional[Literal["data", "state", "lock"]] = None,
    ) -> str:
        parts = [self.prefix]
        if self.with_bot_id:
            parts.append(str(key.bot_id))
        if self.with_business_connection_id and key.business_connection_id:
            parts.append(str(key.business_connection_id))
        parts.append(str(key.chat_id))
        if key.thread_id:
            parts.append(str(key.thread_id))
        parts.append(str(key.user_id))
        if self.with_destiny:
            parts.append(key.destiny)
        elif key.destiny != DEFAULT_DESTINY:
            error_message = (
                "Default key builder is not configured to use key destiny other than the default."
                "\n\nProbably, you should set `with_destiny=True` in for DefaultKeyBuilder."
            )
            raise ValueError(error_message)
        if part:
            parts.append(part)
        return self.separator.join(parts)


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
        """Update date in the storage for key (like dict.update)"""
        current_data = await self.get_data(key=key)
        current_data.update(data)
        await self.set_data(key=key, data=current_data)
        return current_data.copy()

    @abstractmethod
    async def close(self) -> None:  # pragma: no cover
        """Close storage (database connection, file or etc.)"""
        pass
