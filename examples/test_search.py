"""Read-only search smoke test using the Bild Python SDK.

Hand this file to an agent that is getting ``Invalid search key``.
That error is a request-body problem, not auth. Do not call ``/search``
yourself. Use ``client.api.search.files(...)`` so the library sends:

    PUT https://api.getbild.com/search
    Authorization: Bearer <token>
    Accept: application/json
    Content-Type: application/json   (set only because there is a JSON body)

    {"search_key": "<non-empty string>"}

Optional query params: ``pageSize`` and ``from``.

Setup (from the repo root):

    pip install -e .
    copy .env.example .env    # then put the JWT in BILD_API_KEY

    python examples/test_search.py
    python examples/test_search.py bolt
"""

from __future__ import annotations

import json
import sys

from bild import BildAPIError, BildAuthError, BildClient


def _print(label: str, value: object) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(value, indent=2, default=str))


def main(argv: list[str]) -> int:
    search_key = argv[1] if len(argv) > 1 else "bolt"
    if not search_key.strip():
        print("search_key must be a non-empty string")
        return 2

    client = BildClient()  # reads BILD_API_KEY from the environment or .env

    handshake = client.verify()
    _print("BildClient.verify()", handshake)

    result = client.api.search.files(search_key, page_size=5)
    _print(f'client.api.search.files("{search_key}", page_size=5)', result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except ValueError as exc:
        print(f"Setup error: {exc}")
        raise SystemExit(2) from exc
    except BildAuthError as exc:
        print(f"Auth failed ({exc.status_code}): {exc.payload}")
        raise SystemExit(1) from exc
    except BildAPIError as exc:
        print(f"API error ({exc.status_code}): {exc.payload}")
        print(
            "If the payload says Invalid search key, the body key must be "
            "search_key (not query, q, or searchKey). Use this script as-is."
        )
        raise SystemExit(1) from exc
