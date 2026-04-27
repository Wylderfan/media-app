import httpx

from .base import DEFAULT_TIMEOUT, USER_AGENT, MediaDetails, SearchResult

OL_SEARCH = "https://openlibrary.org/search.json"
OL_WORK = "https://openlibrary.org/works/{key}.json"
OL_COVER = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"


def _ol_text(value) -> str:
    if isinstance(value, dict):
        return value.get("value", "")
    return value or ""


class OpenLibraryProvider:
    name = "openlibrary"
    media_types = ("book",)

    def __init__(self) -> None:
        self.enabled = True
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=DEFAULT_TIMEOUT,
        )

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not query.strip():
            return []
        r = self._client.get(OL_SEARCH, params={"q": query, "limit": limit})
        r.raise_for_status()
        results: list[SearchResult] = []
        for doc in r.json().get("docs", [])[:limit]:
            key = doc.get("key")
            if not key:
                continue
            cover = (
                OL_COVER.format(cover_id=doc["cover_i"])
                if doc.get("cover_i")
                else None
            )
            results.append(
                SearchResult(
                    provider=self.name,
                    type="book",
                    external_id=key,
                    title=doc.get("title", "(untitled)"),
                    creators=doc.get("author_name") or [],
                    year=doc.get("first_publish_year"),
                    cover_url=cover,
                    snippet=doc.get("subtitle"),
                )
            )
        return results

    def fetch(self, external_id: str) -> MediaDetails:
        work_key = external_id.removeprefix("/works/").removesuffix(".json")
        r = self._client.get(OL_WORK.format(key=work_key))
        r.raise_for_status()
        data = r.json()
        covers = data.get("covers") or []
        cover = OL_COVER.format(cover_id=covers[0]) if covers else None
        # Author names require a second hop per author; deferring to Phase 3 if it matters.
        author_keys = [
            a.get("author", {}).get("key", "")
            for a in (data.get("authors") or [])
        ]
        return MediaDetails(
            provider=self.name,
            type="book",
            external_id=external_id,
            title=data.get("title", "(untitled)"),
            creators=[k for k in author_keys if k],
            year=None,
            cover_url=cover,
            metadata={"description": _ol_text(data.get("description"))},
        )
