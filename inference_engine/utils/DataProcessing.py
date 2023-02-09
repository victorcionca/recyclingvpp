from datetime import datetime


def from_ms_since_epoch(ms: str) -> datetime:
    return datetime.fromtimestamp(int(ms) / 1000.0)
