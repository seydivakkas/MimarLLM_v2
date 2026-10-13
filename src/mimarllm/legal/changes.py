"""Untrusted candidate mentions of amendment/effectivity/exception language.

No inferred legal effective date or consolidated version is produced.
"""
from __future__ import annotations

import re

from mimarllm.legal.models import (
    ChangeKind, LegalChangeCandidate, LegalLine,
)

_PATTERNS = (
    (ChangeKind.REPEAL_MENTION,
     re.compile(r"yürürlükten\s+kaldırıl|mülga|ilga\s+edil", re.IGNORECASE)),
    (ChangeKind.AMENDMENT_MENTION,
     re.compile(r"değiştirilmi[şs]|değişik\s*[:(]|aşağıdaki\s+şekilde\s+değiş", re.IGNORECASE)),
    (ChangeKind.EFFECTIVITY_MENTION,
     re.compile(r"yürürlüğe\s+gir|yürürlük\s+tarih", re.IGNORECASE)),
    (ChangeKind.EXCEPTION_MENTION,
     re.compile(r"istisna|hariç\s+tutul|saklıdır", re.IGNORECASE)),
)


def find_change_candidates(
    lines: list[LegalLine], line_to_node_id: dict[str, str],
) -> list[LegalChangeCandidate]:
    found: list[LegalChangeCandidate] = []
    for line in lines:
        for kind, pattern in _PATTERNS:
            if pattern.search(line.text):
                found.append(LegalChangeCandidate(
                    candidate_id=f"{line.line_id}:change:{kind.value}",
                    kind=kind, source=line.source, text=line.text,
                    related_node_id=line_to_node_id.get(line.line_id),
                ))
    return found
