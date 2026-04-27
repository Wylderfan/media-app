from dataclasses import dataclass, field
from typing import Any

USER_AGENT = "media-tracker/1.0 (+https://github.com/Wylderfan/media-app)"
DEFAULT_TIMEOUT = 10.0


@dataclass
class SearchResult:
    provider: str
    type: str
    external_id: str
    title: str
    creators: list[str] = field(default_factory=list)
    year: int | None = None
    cover_url: str | None = None
    snippet: str | None = None


@dataclass
class MediaDetails:
    provider: str
    type: str
    external_id: str
    title: str
    creators: list[str] = field(default_factory=list)
    year: int | None = None
    cover_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
