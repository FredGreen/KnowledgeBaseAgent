"""Text utility functions: token estimation, truncation."""

import re


def estimate_tokens(text: str) -> int:
    """Rough token estimation (Chinese ~1.5 chars/token, English ~4 chars/token)."""
    if not text:
        return 0
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def truncate_text(text: str, max_tokens: int) -> tuple[str, int]:
    """Truncate text to fit within max_tokens. Returns (truncated_text, removed_count)."""
    if estimate_tokens(text) <= max_tokens:
        return text, 0
    ratio = max_tokens / estimate_tokens(text)
    cut_pos = int(len(text) * ratio)
    removed = len(text) - cut_pos
    return text[:cut_pos], removed


def summarize_messages(messages: list[dict], max_chars: int = 500) -> str:
    """Summarize recent messages for router context."""
    parts = []
    total = 0
    for msg in reversed(messages):
        content = msg.get("content", "")
        role = msg.get("role", "")
        entry = f"{role}: {content[:100]}"
        if total + len(entry) > max_chars:
            break
        parts.append(entry)
        total += len(entry)
    return "\n".join(reversed(parts))
