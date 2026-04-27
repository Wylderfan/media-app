from .base import DEFAULT_TIMEOUT, USER_AGENT, MediaDetails, SearchResult
from .books import OpenLibraryProvider
from .film_tv import TmdbProvider
from .games import RawgProvider
from .music import MusicBrainzProvider


def get_providers() -> list:
    """Instantiate every provider. Disabled ones are returned with enabled=False."""
    return [
        OpenLibraryProvider(),
        TmdbProvider(),
        RawgProvider(),
        MusicBrainzProvider(),
    ]


__all__ = [
    "DEFAULT_TIMEOUT",
    "USER_AGENT",
    "MediaDetails",
    "SearchResult",
    "OpenLibraryProvider",
    "TmdbProvider",
    "RawgProvider",
    "MusicBrainzProvider",
    "get_providers",
]
