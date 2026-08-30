from __future__ import annotations

import re

BUYING = "buying"
BROWSING = "browsing"
OVERRIDE = "override"
BOUNDARY = "boundary"
OTHER = "other"

_BUYING_RE = re.compile(r"\ba key requirement is:", re.I)
_BROWSING_RE = re.compile(r"\bstill exploring\b", re.I)
_OVERRIDE_RE = re.compile(
    r"(ignore my earlier preference|\bwhat i need is:)",
    re.I,
)
_OVERRIDE_START_RE = re.compile(r"^\s*actually\b", re.I)
_BOUNDARY_RE = re.compile(
    r"don['’]?t have (an additional |a )?preference",
    re.I,
)
_LOOKING_RE = re.compile(
    r"i['’]?m looking for\s+(.+?)"
    r"(?:,?\s*but i['’]?m still exploring|\.\s*a key requirement|\.|$)",
    re.I,
)


def classify_track(message: str) -> str:
    text = message or ""
    if _OVERRIDE_RE.search(text) or _OVERRIDE_START_RE.search(text):
        return OVERRIDE
    if _BOUNDARY_RE.search(text):
        return BOUNDARY
    if _BUYING_RE.search(text):
        return BUYING
    if _BROWSING_RE.search(text):
        return BROWSING
    return OTHER


def looking_for_crumb(message: str) -> str | None:
    if not message:
        return None
    match = _LOOKING_RE.search(message)
    if not match:
        return None
    crumb = re.sub(r"\s+", " ", match.group(1)).strip(" .,;:-")
    return crumb or None
