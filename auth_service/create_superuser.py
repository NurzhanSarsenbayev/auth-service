import argparse
import os
from urllib.parse import urlsplit, urlunsplit

from core.config import settings
from helpers.superuser import ensure_superuser


def _redact_db_url(db_url: str) -> str:
    try:
        parts = urlsplit(db_url)

        # If there is no userinfo, there's nothing sensitive to hide
        if parts.username is None:
            return db_url

        host = parts.hostname or "***"
        port = f":{parts.port}" if parts.port else ""
        user = parts.username

        # Keep DB name/path, hide password
        netloc = f"{user}:***@{host}{port}"
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        # Last-resort: never leak the original URL
        return "***redacted***"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create/ensure superuser")
    parser.add_argument("--db", type=str, help="Database URL (optional)")
    args = parser.parse_args()

    url = args.db or os.getenv("DB_URL") or settings.database_url
    url = url.replace("+asyncpg", "")

    print(f"Using database URL: {_redact_db_url(url)}")
    ensure_superuser(url)


if __name__ == "__main__":
    main()
