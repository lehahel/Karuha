from .base import BaseStorage, StorageMeta
from .memory import MemoryStorage


def get_storage() -> BaseStorage:
    """Get current storage instance or create new one"""
    if StorageMeta._instance is None:
        print("creating new storage")
        StorageMeta._instance = MemoryStorage()
    return StorageMeta._instance
