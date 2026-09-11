# moderation.py

import re
from pathlib import Path

# Downloaded from:
# https://raw.githubusercontent.com/darwiin/french-badwords-list/master/list.txt
# One word (or phrase) per line.
BADWORDS_FILE = Path(__file__).resolve().parent / "badwords.txt"

# Characters considered "letters" for boundary detection. Digits and symbols
# (used in leetspeak substitutions like "!mb3c!l3") are deliberately excluded,
# so a banned word is still caught even if it starts or ends with one of them.
_LETTERS = "a-zA-ZàâäéèêëïîôöùûüçñÀÂÄÉÈÊËÏÎÔÖÙÛÜÇÑ"


def _load_banned_words() -> set[str]:
    if not BADWORDS_FILE.exists():
        return set()

    words = set()
    for line in BADWORDS_FILE.read_text(encoding="utf-8").splitlines():
        word = line.strip().lower()
        if word:
            words.add(word)
    return words


BANNED_WORDS = _load_banned_words()

_BANNED_PATTERN = (
    re.compile(
        rf"(?<![{_LETTERS}])(" + "|".join(re.escape(word) for word in BANNED_WORDS) + rf")(?![{_LETTERS}])",
        re.IGNORECASE,
    )
    if BANNED_WORDS
    else None
)


def contains_banned_word(text: str) -> bool:
    """Check whether text contains a banned word, ignoring case and leetspeak-friendly boundaries."""
    return bool(_BANNED_PATTERN and _BANNED_PATTERN.search(text))