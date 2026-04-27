import os

import httpx

from .base import DEFAULT_TIMEOUT, MediaDetails, SearchResult

MB_RELEASE_GROUP = "https://musicbrainz.org/ws/2/release-group"
MB_RELEASE_GROUP_DETAIL = "https://musicbrainz.org/ws/2/release-group/{mbid}"
COVER_ART = "https://coverartarchive.org/release-group/{mbid}/front-250"


def _rg_year(raw: str | None) -> int | None:
    if not raw:
        return None
    head = raw[:4]
    return int(head) if head.isdigit() else None


def _rg_artists(item: dict) -> list[str]:
    return [
        ac.get("artist", {}).get("name") or ac.get("name", "")
        for ac in (item.get("artist-credit") or [])
        if ac.get("artist") or ac.get("name")
    ]


class MusicBrainzProvider:
    name = "musicbrainz"
    media_types = ("album",)

    def __init__(self, user_agent: str | None = None) -> None:
        self._user_agent = user_agent if user_agent is not None else os.getenv(
            "MUSICBRAINZ_USER_AGENT", ""
        )
        # MusicBrainz requires a contact-bearing UA per their etiquette; refuse if absent.
        self.enabled = bool(self._user_agent.strip())
        self._client = httpx.Client(
            headers={"User-Agent": self._user_agent or "media-tracker/1.0"},
            timeout=DEFAULT_TIMEOUT,
        )

    def _cover(self, mbid: str) -> str | None:
        url = COVER_ART.format(mbid=mbid)
        try:
            head = self._client.head(url, follow_redirects=True)
        except httpx.HTTPError:
            return None
        return url if head.status_code == 200 else None

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not self.enabled or not query.strip():
            return []
        r = self._client.get(
            MB_RELEASE_GROUP,
            params={"query": query, "fmt": "json", "limit": limit},
        )
        r.raise_for_status()
        results: list[SearchResult] = []
        for rg in r.json().get("release-groups", [])[:limit]:
            mbid = rg.get("id")
            if not mbid:
                continue
            results.append(
                SearchResult(
                    provider=self.name,
                    type="album",
                    external_id=mbid,
                    title=rg.get("title", "(untitled)"),
                    creators=_rg_artists(rg),
                    year=_rg_year(rg.get("first-release-date")),
                    cover_url=self._cover(mbid),
                    snippet=rg.get("primary-type"),
                )
            )
        return results

    def fetch(self, external_id: str) -> MediaDetails:
        r = self._client.get(
            MB_RELEASE_GROUP_DETAIL.format(mbid=external_id),
            params={"fmt": "json", "inc": "artist-credits"},
        )
        r.raise_for_status()
        data = r.json()
        return MediaDetails(
            provider=self.name,
            type="album",
            external_id=external_id,
            title=data.get("title", "(untitled)"),
            creators=_rg_artists(data),
            year=_rg_year(data.get("first-release-date")),
            cover_url=self._cover(external_id),
            metadata={
                "primary_type": data.get("primary-type"),
                "secondary_types": data.get("secondary-types") or [],
            },
        )
