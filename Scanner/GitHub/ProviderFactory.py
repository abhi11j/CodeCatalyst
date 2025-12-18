"""
Factory for suggestion providers. Providers can register themselves by key and
clients can request instances via `create`.
"""
from typing import Type, Dict, Callable, Any
from Scanner.GitHub.Interface.ISearchProvider import ISearchProvider


class ProviderFactory:
    _registry: Dict[str, Callable[..., ISearchProvider]] = {}

    @classmethod
    def register(cls, key: str, creator: Callable[..., ISearchProvider]):
        cls._registry[key] = creator

    @classmethod
    def create(cls, key: str, *args, **kwargs) -> ISearchProvider:
        creator = cls._registry.get(key)
        if not creator:
            raise KeyError(f"Provider not registered: {key}")
        return creator(*args, **kwargs)

    @classmethod
    def registered_keys(cls):
        return list(cls._registry.keys())
