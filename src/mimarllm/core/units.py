"""Explicit drawing units and evidence-gated scale calibration (no inferred legality).

The INSUNITS header is *metadata*, not independent proof of drawing correctness.
Caller confirmation is required before converting CAD lengths to physical metres.
"""
from __future__ import annotations

from enum import Enum
from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LengthUnit(str, Enum):
    UNKNOWN = "unknown"
    MILLIMETRE = "mm"
    CENTIMETRE = "cm"
    METRE = "m"
    INCH = "in"
    FOOT = "ft"


class CalibrationState(str, Enum):
    UNKNOWN = "UNKNOWN"
    INFERRED = "INFERRED"
    CONFIRMED = "CONFIRMED"
    CONFLICT = "CONFLICT"


class CalibrationMethod(str, Enum):
    HEADER_UNITS = "HEADER_UNITS"
    DIMENSION = "DIMENSION"
    GRAPHIC_SCALE = "GRAPHIC_SCALE"
    USER_REFERENCE = "USER_REFERENCE"


_METRES = {
    LengthUnit.MILLIMETRE: 0.001,
    LengthUnit.CENTIMETRE: 0.01,
    LengthUnit.METRE: 1.0,
    LengthUnit.INCH: 0.0254,
    LengthUnit.FOOT: 0.3048,
}

# Deliberately restricted to the common DXF header codes understood by V0.1.
_DXF_INSUNITS = {1: LengthUnit.INCH, 2: LengthUnit.FOOT,
                 4: LengthUnit.MILLIMETRE, 5: LengthUnit.CENTIMETRE,
                 6: LengthUnit.METRE}


class CalibrationError(ValueError):
    """Missing or unsafe physical scale evidence."""


class UnitCalibration(BaseModel):
    """Metres per drawing-source unit, never derived from drawing extent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    state: CalibrationState = CalibrationState.UNKNOWN
    source_unit: LengthUnit = LengthUnit.UNKNOWN
    metres_per_unit: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    method: CalibrationMethod | None = None
    evidence_ids: tuple[str, ...] = ()
    note: str | None = None

    @model_validator(mode="after")
    def validate_evidence(self) -> "UnitCalibration":
        if self.state in {CalibrationState.UNKNOWN, CalibrationState.CONFLICT}:
            if self.metres_per_unit is not None or self.method is not None:
                raise ValueError("unknown/conflicting calibration cannot have a usable scale")
        else:
            if self.metres_per_unit is None or self.method is None:
                raise ValueError("calibration needs explicit method and finite scale")
            if not self.evidence_ids or any(not x.strip() for x in self.evidence_ids):
                raise ValueError("calibration needs traceable source evidence")
        return self

    @classmethod
    def from_dxf_insunits(cls, code: int, *, user_confirmed: bool = False) -> "UnitCalibration":
        unit = _DXF_INSUNITS.get(code, LengthUnit.UNKNOWN)
        if unit == LengthUnit.UNKNOWN:
            return cls(note=f"DXF INSUNITS={code} not supported or unset")
        return cls(
            state=CalibrationState.CONFIRMED if user_confirmed else CalibrationState.INFERRED,
            source_unit=unit, metres_per_unit=_METRES[unit],
            method=CalibrationMethod.HEADER_UNITS,
            evidence_ids=("DXF:$INSUNITS",),
            note="Header units reviewed by user" if user_confirmed else "Header not independently confirmed",
        )

    @classmethod
    def from_reference(
        cls, *, source_distance: float, known_distance_metres: float,
        evidence_id: str, method: CalibrationMethod, user_confirmed: bool = False,
    ) -> "UnitCalibration":
        if method == CalibrationMethod.HEADER_UNITS:
            raise CalibrationError("Use from_dxf_insunits for header units")
        if (not all(isfinite(x) and x > 0 for x in (source_distance, known_distance_metres))
                or not evidence_id.strip()):
            raise CalibrationError("Reference requires positive finite distances and source ID")
        ratio = known_distance_metres / source_distance
        if not isfinite(ratio) or ratio <= 0:
            raise CalibrationError("Invalid physical conversion factor")
        return cls(
            state=CalibrationState.CONFIRMED if user_confirmed else CalibrationState.INFERRED,
            source_unit=LengthUnit.UNKNOWN, metres_per_unit=ratio, method=method,
            evidence_ids=(evidence_id,),
        )

    def length_metres(self, source_length: float) -> float:
        if self.state != CalibrationState.CONFIRMED or self.metres_per_unit is None:
            raise CalibrationError("Confirmed physical calibration is required")
        if not isfinite(source_length) or source_length < 0:
            raise CalibrationError("Length must be finite and non-negative")
        answer = source_length * self.metres_per_unit
        if not isfinite(answer):
            raise CalibrationError("Physical length overflow")
        return answer

    def area_square_metres(self, source_area: float) -> float:
        if self.state != CalibrationState.CONFIRMED or self.metres_per_unit is None:
            raise CalibrationError("Confirmed physical calibration is required")
        if not isfinite(source_area) or source_area < 0:
            raise CalibrationError("Area must be finite and non-negative")
        answer = source_area * self.metres_per_unit**2
        if not isfinite(answer):
            raise CalibrationError("Physical area overflow")
        return answer
