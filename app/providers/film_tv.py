import os

import httpx

from .base import DEFAULT_TIMEOUT, USER_AGENT, MediaDetails, SearchResult

TMDB_MULTI = "https://api.themoviedb.org/3/search/multi"
TMDB_DETAIL = "https://api.themoviedb.org/3/{kind}/{id}"
TMDB_IMAGE = "https://image.tmdb.org/t/p/w342{path}"

# TMDB multi-search returns mixed types; we only care about these two.
_TMDB_TYPE_MAP = {"movie": "film", "tv": "tv"}


def _tmdb_year(item: dict) -> int | None:
    raw = item.get("release_date") or item.get("first_air_date") or ""
    return int(raw[:4]) if raw[:4].isdigit() else None


def _tmdb_cover(path: str | None) -> str | None:
    return TMDB_IMAGE.format(path=path) if path else None


class TmdbProvider:
    name = "tmdb"
    media_types = ("film", "tv")

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("TMDB_API_KEY", "")
        self.enabled = bool(self._api_key)
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=DEFAULT_TIMEOUT,
        )

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not self.enabled or not query.strip():
            return []
        r = self._client.get(
            TMDB_MULTI,
            params={"api_key": self._api_key, "query": query},
        )
        r.raise_for_status()
        results: list[SearchResult] = []
        for item in r.json().get("results", []):
            kind = item.get("media_type")
            internal = _TMDB_TYPE_MAP.get(kind)
            if not internal:
                continue
            title = item.get("title") or item.get("name") or "(untitled)"
            results.append(
                SearchResult(
                    provider=self.name,
                    type=internal,
                    external_id=f"{kind}:{item['id']}",
                    title=title,
                    creators=[],  # populated by fetch (credits endpoint)
                    year=_tmdb_year(item),
                    cover_url=_tmdb_cover(item.get("poster_path")),
                    snippet=item.get("overview"),
                )
            )
            if len(results) >= limit:
                break
        return results

    def fetch(self, external_id: str) -> MediaDetails:
        kind, raw_id = external_id.split(":", 1)
        internal = _TMDB_TYPE_MAP.get(kind)
        if not internal:
            raise ValueError(f"unsupported tmdb kind: {kind!r}")
        r = self._client.get(
            TMDB_DETAIL.format(kind=kind, id=raw_id),
            params={"api_key": self._api_key, "append_to_response": "credits"},
        )
        r.raise_for_status()
        data = r.json()
        title = data.get("title") or data.get("name") or "(untitled)"
        crew = data.get("credits", {}).get("crew", [])
        directors = [c["name"] for c in crew if c.get("job") == "Director"]
        return MediaDetails(
            provider=self.name,
            type=internal,
            external_id=external_id,
            title=title,
            creators=directors,
            year=_tmdb_year(data),
            cover_url=_tmdb_cover(data.get("poster_path")),
            metadata={
                "overview": data.get("overview", ""),
                "runtime": data.get("runtime") or data.get("episode_run_time"),
                "genres": [g["name"] for g in data.get("genres", [])],
            },
        )
