import re

BLOCK_WORDS = {
    "바보",
    "멍청이",
    "죽어",
}

PERSONAL_INFO_PATTERNS = [
    r"\b\d{3}[-]?\d{4}[-]?\d{4}\b",
    r"\b\d{6}[-]?\d{7}\b",
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    r"카카오톡|라인|텔레그램|인스타|디스코드",
]


class ModerationResult:
    def __init__(self, allowed: bool, reason: str | None = None):
        self.allowed = allowed
        self.reason = reason


def moderate_message(message: str) -> ModerationResult:
    lowered = message.lower()

    for word in BLOCK_WORDS:
        if word in lowered:
            return ModerationResult(False, "BLOCK_WORD")

    for pattern in PERSONAL_INFO_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return ModerationResult(False, "PERSONAL_INFO")

    if len(message) > 500:
        return ModerationResult(False, "TOO_LONG")

    return ModerationResult(True)
