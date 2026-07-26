def format_duration(start_ts: int, end_ts: int) -> str:
    """Format a millisecond timestamp pair into a human-readable duration string."""
    duration_s = (end_ts - start_ts) / 1000 if end_ts > start_ts else 0
    mins = int(duration_s // 60)
    secs = int(duration_s % 60)
    return f"{mins}:{secs:02d} min" if mins > 0 else f"{secs}s"
