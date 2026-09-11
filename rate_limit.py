# rate_limit.py

import time
from collections import defaultdict

from fastapi import HTTPException, Request

# Maps a limiter key (e.g. "comments") to { client_ip: [timestamps] }.
_request_log: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))


def rate_limiter(key: str, max_requests: int, window_seconds: float):
    """
    Returns a FastAPI dependency that limits a client IP to `max_requests`
    calls per `window_seconds`, tracked separately per `key` (e.g. one
    limiter for comment creation, another for image uploads).
    """

    def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        timestamps = _request_log[key][client_ip]

        # Drop timestamps outside the current window.
        cutoff = now - window_seconds
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

        if len(timestamps) >= max_requests:
            retry_after = window_seconds - (now - timestamps[0])
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Try again in {retry_after:.0f} seconds.",
                headers={"Retry-After": str(int(retry_after) + 1)},
            )

        timestamps.append(now)

    return dependency


def reset_rate_limits() -> None:
    """Clears all tracked requests. Used by the test suite between tests."""
    _request_log.clear()