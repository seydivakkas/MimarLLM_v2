"""027: Strict, source-locked VLM *suggestions*, never DrawingIR or rule changes."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class VlmFailure(ValueError):
    """Redacted, fail-closed local VLM failure."""


class VlmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    frame_id: str = Field(min_length=1, max_length=120)
    entity_ids: tuple[str, ...] = Field(min_length=1, max_length=48)
    question: str = Field(min_length=1, max_length=320)
    reviewer_label: str = Field(min_length=1, max_length=80)

    @model_validator(mode="after")
    def distinct(self) -> "VlmRequest":
        if len(set(self.entity_ids)) != len(self.entity_ids):
            raise ValueError("Duplicate entity IDs")
        return self


class ModelSuggestion(BaseModel):
    """Untrusted model data: deliberately NO dimensions, approval or status fields."""
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
    entity_ids: tuple[str, ...] = Field(min_length=1, max_length=8)
    kind: Literal[
        "WALL_CANDIDATE", "OPENING_CANDIDATE", "ANNOTATION_CANDIDATE",
        "UNCLASSIFIED", "NEEDS_HUMAN_REVIEW",
    ]
    commentary: str = Field(min_length=1, max_length=320)


class ModelOnlyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    suggestions: tuple[ModelSuggestion, ...] = Field(max_length=4)


class VlmResult(BaseModel):
    """Source-owned envelope: none of these authoritative IDs originate from model."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["027-0.1"] = "027-0.1"
    status: Literal["UNVERIFIED_VLM_SUGGESTION"] = "UNVERIFIED_VLM_SUGGESTION"
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    frame_id: str
    source_entity_ids: tuple[str, ...]
    reviewer_label: str
    model_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mmproj_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_mode: Literal["CPU_FALLBACK", "GPU_BUDGETED"]
    suggestions: tuple[ModelSuggestion, ...]
    legal_gate: Literal["REGULATORY_LOCKED"] = "REGULATORY_LOCKED"
    can_modify_drawing: Literal[False] = False
    can_approve_regulations: Literal[False] = False


def parse_model_response(text: str, selected_ids: tuple[str, ...]) -> ModelOnlyPayload:
    if len(text.encode("utf-8")) > 8192:
        raise VlmFailure("LOCAL_MODEL_OUTPUT_TOO_LARGE")
    try:
        output = ModelOnlyPayload.model_validate_json(text)
    except (ValueError, TypeError) as exc:
        raise VlmFailure("LOCAL_MODEL_SCHEMA_INVALID") from exc
    allowed = set(selected_ids)
    if any(not set(item.entity_ids) <= allowed or len(set(item.entity_ids)) != len(item.entity_ids)
           for item in output.suggestions):
        raise VlmFailure("LOCAL_MODEL_UNKNOWN_SOURCE")
    return output
