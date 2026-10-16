"""028: versioned pedagogical rubric catalog; educational pilot, not official grades.

The rubric does not derive educational merit from CAD geometry or VLM text.
All numeric levels are explicit, locally entered human review *claims*.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


RUBRIC_VERSION = "028.0.1"


class Axis(str, Enum):
    CONTEXT = "CONTEXT"
    CONCEPT = "CONCEPT"
    FUNCTION = "FUNCTION"
    SPATIAL = "SPATIAL"
    STRUCTURE = "STRUCTURE"
    ENVIRONMENT = "ENVIRONMENT"
    REPRESENTATION = "REPRESENTATION"
    PROCESS = "PROCESS"


class AxisDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    axis: Axis
    title_tr: str
    default_weight: int = Field(gt=0, le=100)


class Criterion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    criterion_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]{3,64}$")
    axis: Axis
    title_tr: str = Field(min_length=3, max_length=150)
    evidence_hint_tr: str = Field(min_length=3, max_length=220)
    min_year: int = Field(ge=1, le=4)
    max_year: int = Field(default=4, ge=1, le=4)
    internal_weight: int = Field(default=1, ge=1, le=10)

    @model_validator(mode="after")
    def year_window(self) -> "Criterion":
        if self.min_year > self.max_year:
            raise ValueError("Invalid pedagogical year window")
        return self


class RubricCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rubric_version: Literal["028.0.1"] = RUBRIC_VERSION
    use: Literal["LOCAL_PEDAGOGICAL_PILOT_NOT_OFFICIAL"] = "LOCAL_PEDAGOGICAL_PILOT_NOT_OFFICIAL"
    axes: tuple[AxisDefinition, ...]
    criteria: tuple[Criterion, ...]

    @model_validator(mode="after")
    def complete(self) -> "RubricCatalog":
        if len(self.axes) != 8 or {x.axis for x in self.axes} != set(Axis):
            raise ValueError("Exactly eight unique architectural pedagogical axes required")
        if sum(axis.default_weight for axis in self.axes) != 100:
            raise ValueError("Default weights must sum to 100")
        ids=[c.criterion_id for c in self.criteria]
        if len(ids)!=len(set(ids)):
            raise ValueError("Duplicate criterion")
        for year in range(1,5):
            if not any(c.min_year <= year <= c.max_year for c in self.criteria):
                raise ValueError("Empty year scope")
        return self


AXES = (
    AxisDefinition(axis=Axis.CONTEXT, title_tr="Yer ve bağlam okuması",default_weight=10),
    AxisDefinition(axis=Axis.CONCEPT, title_tr="Kavramsal yaklaşım",default_weight=20),
    AxisDefinition(axis=Axis.FUNCTION,title_tr="İşlevsel program",default_weight=15),
    AxisDefinition(axis=Axis.SPATIAL,title_tr="Mekânsal organizasyon",default_weight=15),
    AxisDefinition(axis=Axis.STRUCTURE,title_tr="Taşıyıcı ve yapım yaklaşımı",default_weight=10),
    AxisDefinition(axis=Axis.ENVIRONMENT,title_tr="İklim ve çevresel yaklaşım",default_weight=10),
    AxisDefinition(axis=Axis.REPRESENTATION,title_tr="Mimari temsil ve iletişim",default_weight=12),
    AxisDefinition(axis=Axis.PROCESS,title_tr="Tasarım süreci ve öz değerlendirme",default_weight=8),
)
C = Criterion
CRITERIA = (
    C(criterion_id="CONTEXT_OBSERVATION",axis=Axis.CONTEXT,title_tr="Yakın çevreyi gözlemleme",
      evidence_hint_tr="Bağlamla ilişkili plan/çizim konumunu ve insan incelemesini belirtin",min_year=1),
    C(criterion_id="CONTEXT_HISTORIC",axis=Axis.CONTEXT,title_tr="Tarihsel-kültürel katmanları ilişkilendirme",
      evidence_hint_tr="Kaynakla ilişkili yorum ve inceleme kaydı",min_year=3),
    C(criterion_id="CONCEPT_INTENT",axis=Axis.CONCEPT,title_tr="Tasarım fikrini gerekçelendirme",
      evidence_hint_tr="Kararın gösterildiği çizgi ve insan açıklaması",min_year=1),
    C(criterion_id="CONCEPT_THEORY",axis=Axis.CONCEPT,title_tr="Kavramsal tutarlılığı derinleştirme",
      evidence_hint_tr="Kuramsal kararın çizime yansıması hakkında insan yorumu",min_year=3),
    C(criterion_id="FUNCTION_NEEDS",axis=Axis.FUNCTION,title_tr="Kullanıcı ihtiyaçlarını araştırma",
      evidence_hint_tr="Kaynak çizim ve program kararı için insan açıklaması",min_year=1),
    C(criterion_id="FUNCTION_ACCESS",axis=Axis.FUNCTION,title_tr="İşlevler arası erişilebilir ilişki",
      evidence_hint_tr="Tasarım tercihi; resmî yönetmelik değerlendirmesi değil",min_year=3),
    C(criterion_id="SPATIAL_BASIC",axis=Axis.SPATIAL,title_tr="Temel mekânsal ilişkiler",
      evidence_hint_tr="İlişkili çizim kaynak kimliği ve insan kararı",min_year=1),
    C(criterion_id="SPATIAL_SEQUENCE",axis=Axis.SPATIAL,title_tr="Dolaşım ve mekânsal sekans",
      evidence_hint_tr="Dolaşımın plan üzerinde gözlemlendiği kaynak çizgi",min_year=2),
    C(criterion_id="STRUCTURE_CONCEPT",axis=Axis.STRUCTURE,title_tr="Taşıyıcı sistem fikri",
      evidence_hint_tr="Kütle/kurgu ile strüktür ilişkisi; statik uygunluk değildir",min_year=2),
    C(criterion_id="STRUCTURE_COORDINATION",axis=Axis.STRUCTURE,title_tr="Taşıyıcı sistem koordinasyonu",
      evidence_hint_tr="Birleşim ve detaylar için eğitmen incelemesi",min_year=4),
    C(criterion_id="ENVIRONMENT_ORIENTATION",axis=Axis.ENVIRONMENT,title_tr="İklime yönelim ve yerleşim",
      evidence_hint_tr="Yerleşim kararını gösteren çizim konumu",min_year=2),
    C(criterion_id="ENVIRONMENT_PASSIVE",axis=Axis.ENVIRONMENT,title_tr="Pasif çevresel stratejiler",
      evidence_hint_tr="Güneş, gölge ve havalandırma kararları için insan yorumu",min_year=3),
    C(criterion_id="REPRESENTATION_PLAN",axis=Axis.REPRESENTATION,title_tr="Plan anlatımının okunurluğu",
      evidence_hint_tr="Okunurluk gözlemi ve kaynak çizgi/pafta ilişkisi",min_year=1),
    C(criterion_id="REPRESENTATION_COHERENCE",axis=Axis.REPRESENTATION,title_tr="Plan ve kesitin anlatım bütünlüğü",
      evidence_hint_tr="Pafta referansı; yanlış sayfa eşlemesine izin verilmez",min_year=2),
    C(criterion_id="PROCESS_REFLECTION",axis=Axis.PROCESS,title_tr="Kararlara eleştirel bakış",
      evidence_hint_tr="Öğrencinin tartışılmış tasarım gerekçesine insan yorumu",min_year=1),
    C(criterion_id="PROCESS_ITERATION",axis=Axis.PROCESS,title_tr="Alternatifler ve revizyon gerekçeleri",
      evidence_hint_tr="Önceki tasarım aşamaları için eğitmen kaynak incelemesi",min_year=4),
)
DEFAULT_CATALOG = RubricCatalog(axes=AXES,criteria=CRITERIA)


def profile(year: int) -> dict:
    if type(year) is not int or year not in (1,2,3,4):
        raise ValueError("Only architecture studio levels 1-4 supported")
    included=tuple(c for c in DEFAULT_CATALOG.criteria if c.min_year<=year<=c.max_year)
    return {
        "rubric_version":DEFAULT_CATALOG.rubric_version,
        "academic_year":year,
        "profile_kind":"LOCAL_PEDAGOGICAL_PILOT_NOT_OFFICIAL",
        "axes":[{
            **axis.model_dump(mode="json"),
            "active":any(c.axis==axis.axis for c in included),
        } for axis in DEFAULT_CATALOG.axes],
        "criteria":[c.model_dump(mode="json") for c in included],
        "excluded_higher_year_criteria":[c.criterion_id for c in DEFAULT_CATALOG.criteria
                                          if c.min_year>year],
        "scale_levels":{
            "0":"İnsan değerlendirmesi: gösterilmedi",
            "1":"İnsan değerlendirmesi: çok sınırlı",
            "2":"İnsan değerlendirmesi: gelişmekte",
            "3":"İnsan değerlendirmesi: yeterli taslak",
            "4":"İnsan değerlendirmesi: güçlü taslak",
        },
        "official_grade":False,
        "legal_gate":"REGULATORY_LOCKED",
    }
