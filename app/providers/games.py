import os

import httpx

from .base import DEFAULT_TIMEOUT, USER_AGENT, MediaDetails, SearchResult

RAWG_LIST = "https://api.rawg.io/api/games"
RAWG_DETAIL = "https://api.rawg.io/api/games/{id}"


def _rawg_year(raw: str | None) -> int | None:
    if not raw:
        return None
    head = raw[:4]
    return int(head) if head.isdigit() else None


class RawgProvider:
    name = "rawg"
    media_types = ("game",)

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("RAWG_API_KEY", "")
        self.enabled = bool(self._api_key)
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=DEFAULT_TIMEOUT,
        )

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not self.enabled or not query.strip():
            return []
        r = self._client.get(
            RAWG_LIST,
            params={"key": self._api_key, "search": query, "page_size": limit},
        )
        r.raise_for_status()
        results: list[SearchResult] = []
        for item in r.json().get("results", [])[:limit]:
            developers = [d["name"] for d in (item.get("developers") or [])]
            results.append(
                SearchResult(
                    provider=self.name,
                    type="game",
                    external_id=str(item["id"]),
                    title=item.get("name", "(untitled)"),
                    creators=developers,
                    year=_rawg_year(item.get("released")),
                    cover_url=item.get("background_image"),
                    snippet=None,
                )
            )
        return results

    def fetch(self, external_id: str) -> MediaDetails:
        r = self._client.get(
            RAWG_DETAIL.format(id=external_id),
            params={"key": self._api_key},
        )
        r.raise_for_status()
        data = r.json()
        developers = [d["name"] for d in (data.get("developers") or [])]
        return MediaDetails(
            provider=self.name,
            type="game",
            external_id=external_id,
            title=data.get("name", "(untitled)"),
            creators=developers,
            year=_rawg_year(data.get("released")),
            cover_url=data.get("background_image"),
            metadata={
                "description": data.get("description_raw", ""),
                "platforms": [
                    p["platform"]["name"] for p in (data.get("platforms") or [])
                ],
                "genres": [g["name"] for g in (data.get("genres") or [])],
            },
        )
