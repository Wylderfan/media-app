"""Exercise every enabled provider with a fixed query and print normalized results."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.providers import get_providers  # noqa: E402

QUERIES = {
    "book": "dune",
    "film": "blade runner",
    "tv": "breaking bad",
    "game": "portal",
    "album": "kid a",
}


def main() -> int:
    providers = get_providers()
    for p in providers:
        marker = "[ok]" if p.enabled else "[off]"
        types = "/".join(p.media_types)
        print(f"\n=== {marker} {p.name} ({types}) ===")
        if not p.enabled:
            print("  disabled — required env var missing")
            continue
        query = QUERIES[p.media_types[0]]
        try:
            results = p.search(query, limit=3)
        except Exception as e:
            print(f"  search failed: {type(e).__name__}: {e}")
            continue
        print(f"  query: {query!r} -> {len(results)} result(s)")
        for r in results:
            year = f" ({r.year})" if r.year else ""
            creators = ", ".join(r.creators[:2]) if r.creators else "-"
            cover = "yes" if r.cover_url else "no"
            print(f"    [{r.type}] {r.title}{year} - {creators}")
            print(f"       id={r.external_id}  cover={cover}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
