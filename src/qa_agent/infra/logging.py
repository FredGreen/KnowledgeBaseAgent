"""Logging configuration with sensitive data redaction."""

import logging
import re
import sys


def redact(text: str) -> str:
    """Redact API keys and sensitive patterns from text."""
    text = re.sub(r'(sk-[a-zA-Z0-9]{20})[a-zA-Z0-9]+', r'\1****', text)
    text = re.sub(r'(key-[a-zA-Z0-9]{8})[a-zA-Z0-9]+', r'\1****', text)
    text = re.sub(r'([a-f0-9]{32})[a-f0-9]+', r'\1****', text)
    return text


class RedactFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            record.args = tuple(
                redact(a) if isinstance(a, str) else a
                for a in record.args
            )
        return True


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure application logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger("qa_agent")
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)-7s %(name)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(fmt)
        handler.addFilter(RedactFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
