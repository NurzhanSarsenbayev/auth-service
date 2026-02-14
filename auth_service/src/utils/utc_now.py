from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC timestamp (compatible with timestamp without time zone columns)."""
    return datetime.now(UTC).replace(tzinfo=None)
