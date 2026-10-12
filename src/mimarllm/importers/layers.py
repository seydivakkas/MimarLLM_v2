"""Conservative lexical layer hints. Never confirms architectural semantics."""
from __future__ import annotations
import re
import unicodedata


def layer_hint(layer_name: str) -> str | None:
    """Return only a search/review *candidate*, never a verified wall/door/room."""
    normalized = unicodedata.normalize("NFKD", layer_name).casefold()
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    normalized = normalized.replace("ı", "i")
    tokens = set(filter(None, re.split(r"[^a-z0-9]+", normalized)))
    candidates = {
        "WALL_CANDIDATE": {"duvar", "wall", "walls"},
        "DOOR_CANDIDATE": {"kapi", "door", "doors"},
        "WINDOW_CANDIDATE": {"pencere", "window", "windows"},
        "ROOM_LABEL_CANDIDATE": {"mahal", "room", "oda"},
        "DIMENSION_CANDIDATE": {"olcu", "dim", "dimension"},
    }
    matched = [kind for kind, terms in candidates.items() if tokens & terms]
    return matched[0] if len(matched) == 1 else None
