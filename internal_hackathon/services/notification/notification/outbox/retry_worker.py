"""Retry policy used by provider workers."""


def next_state(retry_count: int, max_retries: int = 5) -> tuple[str, int]:
    retry_count += 1
    return ("dead_letter" if retry_count >= max_retries else "failed", retry_count)
