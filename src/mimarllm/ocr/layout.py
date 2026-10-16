"""Source-located PAGE LAYOUT CANDIDATES, never verified title-block semantics."""
from __future__ import annotations

from enum import Enum
from math import isfinite
from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.core.models import TextCandidate
from mimarllm.core.ir import SHA256_PATTERN

class LayoutZone(str, Enum):
    LOWER_RIGHT_TEXT_CLUSTER = "LOWER_RIGHT_TEXT_CLUSTER"
    TOP_MARGIN_TEXT_CLUSTER = "TOP_MARGIN_TEXT_CLUSTER"
    BOTTOM_MARGIN_TEXT_CLUSTER = "BOTTOM_MARGIN_TEXT_CLUSTER"

class LayoutCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_id: str
    document_sha256: str = Field(pattern=SHA256_PATTERN)
    page_index: int = Field(ge=0)
    zone: LayoutZone
    polygon: tuple[tuple[float,float],tuple[float,float],tuple[float,float],tuple[float,float]]
    text_candidate_ids: tuple[str,...] = Field(min_length=1)
    approval_status: str = "REVIEW_REQUIRED"
    source_semantics: str = "POSITION_ONLY_NO_TITLE_BLOCK_CERTIFICATION"

    @model_validator(mode="after")
    def valid_polygon(self):
        if any(not isfinite(v) for p in self.polygon for v in p):
            raise ValueError("Layout polygon has non-finite positions")
        return self

def detect_layout_candidates(
    document_sha256: str, page_index: int, width_pt: float, height_pt: float,
    text: list[TextCandidate], *, max_text: int = 40_000,
) -> tuple[LayoutCandidate,...]:
    """Propose clusters in fixed displayed-page PDF-point zones.

    This is *location evidence only*: it does not identify an architect,
    project, drawing scale, municipality or permit title-block field.
    """
    if (not isfinite(width_pt) or not isfinite(height_pt)
            or width_pt<=0 or height_pt<=0 or len(text)>max_text
            or page_index<0):
        raise ValueError("Invalid PDF page or layout processing budget")
    zones = [
        (LayoutZone.LOWER_RIGHT_TEXT_CLUSTER, (.63*width_pt,.65*height_pt,width_pt,height_pt)),
        (LayoutZone.TOP_MARGIN_TEXT_CLUSTER, (0,0,width_pt,.12*height_pt)),
        (LayoutZone.BOTTOM_MARGIN_TEXT_CLUSTER, (0,.88*height_pt,width_pt,height_pt)),
    ]
    results=[]
    for zone,(left,top,right,bottom) in zones:
        match=[]
        for t in text:
            if t.page_index!=page_index or not t.text.strip():
                continue
            xs=[p[0] for p in t.polygon]
            ys=[p[1] for p in t.polygon]
            if not all(isfinite(x) for x in xs+ys):
                continue
            cx=sum(xs)/4
            cy=sum(ys)/4
            if left<=cx<=right and top<=cy<=bottom:
                match.append(t)
        if not match:
            continue
        xs=[x for t in match for x,_ in t.polygon]
        ys=[y for t in match for _,y in t.polygon]
        box=(max(0,min(xs)),max(0,min(ys)),min(width_pt,max(xs)),min(height_pt,max(ys)))
        if box[0]>=box[2] or box[1]>=box[3]:
            continue
        x0,y0,x1,y1=box
        results.append(LayoutCandidate(
            candidate_id=f"p{page_index}:{zone.value}",
            document_sha256=document_sha256,page_index=page_index,zone=zone,
            polygon=((x0,y0),(x1,y0),(x1,y1),(x0,y1)),
            text_candidate_ids=tuple(t.candidate_id for t in match),
        ))
    return tuple(results)
