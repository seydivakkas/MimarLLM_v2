"""Synthetic unit calibration regression: no implicit metric scale."""
import math

import pytest
from pydantic import ValidationError

from mimarllm.core.units import (
    CalibrationError,
    CalibrationMethod,
    CalibrationState,
    LengthUnit,
    UnitCalibration,
)


@pytest.mark.parametrize("code,unit,metres", [
    (1, LengthUnit.INCH, 0.0254),
    (2, LengthUnit.FOOT, 0.3048),
    (4, LengthUnit.MILLIMETRE, 0.001),
    (5, LengthUnit.CENTIMETRE, 0.01),
    (6, LengthUnit.METRE, 1.0),
])
def test_header_is_not_confirmation(code, unit, metres):
    calibration = UnitCalibration.from_dxf_insunits(code)
    assert calibration.state is CalibrationState.INFERRED
    assert calibration.source_unit is unit
    assert calibration.metres_per_unit == pytest.approx(metres)
    assert calibration.evidence_ids == ("DXF:$INSUNITS",)
    with pytest.raises(CalibrationError):
        calibration.length_metres(500)


def test_explicitly_confirmed_header_converts_length_and_area():
    calibration = UnitCalibration.from_dxf_insunits(4, user_confirmed=True)
    assert calibration.state is CalibrationState.CONFIRMED
    assert calibration.length_metres(2500) == pytest.approx(2.5)
    assert calibration.area_square_metres(4_000_000) == pytest.approx(4.0)


@pytest.mark.parametrize("code", [0, 3, 7, 999])
def test_unrecognised_units_remain_unknown(code):
    calibration = UnitCalibration.from_dxf_insunits(code)
    assert calibration.state is CalibrationState.UNKNOWN
    assert calibration.metres_per_unit is None
    with pytest.raises(CalibrationError):
        calibration.area_square_metres(125.5)


def test_graphic_scale_requires_evidence_and_confirmation():
    pending = UnitCalibration.from_reference(
        source_distance=100, known_distance_metres=2,
        method=CalibrationMethod.GRAPHIC_SCALE,
        evidence_id="p0-scale-bar",
    )
    assert pending.state is CalibrationState.INFERRED
    with pytest.raises(CalibrationError):
        pending.length_metres(10)
    verified = UnitCalibration.from_reference(
        source_distance=100, known_distance_metres=2,
        method=CalibrationMethod.GRAPHIC_SCALE,
        evidence_id="p0-scale-bar", user_confirmed=True,
    )
    assert verified.length_metres(10) == pytest.approx(0.2)
    assert verified.area_square_metres(50) == pytest.approx(0.02)


@pytest.mark.parametrize("distance,metres", [(0, 2), (-2, 2), (2, 0), (2, -1), (float("nan"), 2), (2, float("inf"))])
def test_bad_reference_rejected(distance, metres):
    with pytest.raises(CalibrationError):
        UnitCalibration.from_reference(
            source_distance=distance, known_distance_metres=metres,
            method=CalibrationMethod.DIMENSION, evidence_id="d1",
        )


def test_blank_reference_rejected():
    with pytest.raises(CalibrationError):
        UnitCalibration.from_reference(
            source_distance=2, known_distance_metres=2,
            method=CalibrationMethod.DIMENSION, evidence_id="",
        )


def test_header_cannot_be_used_as_reference():
    with pytest.raises(CalibrationError):
        UnitCalibration.from_reference(
            source_distance=1, known_distance_metres=1,
            method=CalibrationMethod.HEADER_UNITS, evidence_id="fake",
        )


def test_inconsistent_state_rejected():
    with pytest.raises(ValidationError):
        UnitCalibration(state=CalibrationState.CONFIRMED, metres_per_unit=1, method=CalibrationMethod.DIMENSION)
    with pytest.raises(ValidationError):
        UnitCalibration(state=CalibrationState.UNKNOWN, metres_per_unit=1, method=CalibrationMethod.DIMENSION)
    with pytest.raises(ValidationError):
        UnitCalibration(state=CalibrationState.CONFLICT, metres_per_unit=1)


def test_nonfinite_physical_length_rejected():
    verified = UnitCalibration.from_dxf_insunits(6, user_confirmed=True)
    with pytest.raises(CalibrationError):
        verified.length_metres(float("nan"))
    with pytest.raises(CalibrationError):
        verified.area_square_metres(math.inf)


def test_area_is_squared_scale_not_length_scale():
    verified = UnitCalibration.from_dxf_insunits(5, user_confirmed=True)
    assert verified.area_square_metres(10_000) == pytest.approx(1.0)
