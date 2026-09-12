from datetime import datetime, timedelta, timezone

TARGET_SECONDS = 120


def deadline(reported_at: datetime) -> datetime:
    return reported_at + timedelta(seconds=TARGET_SECONDS)


def elapsed(reported_at: datetime, now: datetime | None = None) -> float:
    current = now or datetime.now(timezone.utc)
    return max(0.0, (current - reported_at).total_seconds())


def achieved(reported_at: datetime, now: datetime | None = None) -> bool:
    return elapsed(reported_at, now) <= TARGET_SECONDS
