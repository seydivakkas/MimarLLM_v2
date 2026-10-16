"""Curated *search hints* for Turkish architectural terminology.

These are NOT legal synonyms, official definitions, accepted statutory
equivalences, or statements about an applicable regulation. Opt-in only.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from mimarllm.rag.store import RagStoreError, normalize_search_text, match_expression

LEXICON_VERSION = "architectural-search-hints-v0.1"

# Each row: one trigger and related search expressions. Do NOT turn these
# into substitutions of source LegalAST wording, legal terms or RuleEngine data.
_SEARCH_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ışıklık", ("ışık kuyusu", "aydınlatma boşluğu")),
    ("ışık kuyusu", ("ışıklık",)),
    ("kapı temiz genişliği", ("kapı net genişliği", "kapı geçiş açıklığı")),
    ("kapı net genişliği", ("kapı temiz genişliği",)),
    ("kaçış merdiveni", ("yangın merdiveni",)),
    ("yangın merdiveni", ("kaçış merdiveni",)),
    ("sahanlık", ("merdiven sahanlığı",)),
    ("engelli rampası", ("erişilebilir rampa",)),
    ("erişilebilir rampa", ("engelli rampası",)),
    ("otopark", ("araç park alanı",)),
    ("araç park alanı", ("otopark",)),
    ("havalandırma bacası", ("hava bacası",)),
    ("hava bacası", ("havalandırma bacası",)),
    ("ıslak hacim", ("banyo", "tuvalet")),
)

@dataclass(frozen=True)
class ExpansionPlan:
    version: str
    hints: tuple[str, ...]
    used_triggers: tuple[str, ...]
    advisory: str = "SEARCH_CANDIDATES_ONLY_NOT_LEGAL_EQUIVALENCE"


def expand_architectural_terms(query: str, *, max_hints: int = 6) -> ExpansionPlan:
    """Only match complete normalized word phrases; no fuzzy legal inference."""
    match_expression(query)  # Same 512-char / token safety validation as SQLite.
    if not isinstance(max_hints, int) or not 1 <= max_hints <= 12:
        raise RagStoreError("Architectural search hint budget invalid")
    normalized = normalize_search_text(query)
    words = tuple(re.findall(r"\w+", normalized, flags=re.UNICODE))
    found: list[str] = []
    triggers: list[str] = []
    original_phrases = " ".join(words)
    for trigger, candidates in _SEARCH_HINTS:
        pattern = " ".join(re.findall(r"\w+", normalize_search_text(trigger)))
        if not pattern:
            continue
        # \\b handles complete lexical term boundaries and avoids part-words.
        if re.search(r"(?<!\w)" + re.escape(pattern) + r"(?!\w)", original_phrases):
            triggers.append(trigger)
            for candidate in candidates:
                term = normalize_search_text(candidate)
                if term != normalized and term not in found:
                    found.append(term)
                if len(found) >= max_hints:
                    break
        if len(found) >= max_hints:
            break
    return ExpansionPlan(
        version=LEXICON_VERSION,
        hints=tuple(found),
        used_triggers=tuple(triggers),
    )
