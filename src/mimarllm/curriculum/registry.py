"""Versioned 55-module curriculum catalogue. It does not mean 55 implementations.

Curriculum-intended module availability is independent of code deployment
and regulatory applicability; all catalog-only modules are unscored.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Grade = Literal[1, 2, 3, 4]


@dataclass(frozen=True)
class CurriculumModule:
    code: str
    title: str
    introduced_grade: int
    implementation_state: str = "CATALOG_ONLY"
    grading_enabled: bool = False
    regulatory_approved: bool = False

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "title": self.title,
            "introduced_grade": self.introduced_grade,
            "implementation_state": self.implementation_state,
            "grading_enabled": self.grading_enabled,
            "regulatory_approved": self.regulatory_approved,
        }


_CATALOGUE = (
    ("MOD-101", "Katman ve Çizgi Kalınlığı Hiyerarşisi Denetçisi", 1),
    ("MOD-102", "Geometri Temizliği ve Köşe Kenetleme Analizi", 1),
    ("MOD-103", "Birim, Ölçek ve Ölçülendirme Doğrulayıcı", 1),
    ("MOD-104", "Teknik Sembol, Kot ve Kuzey Oku Kontrolü", 1),
    ("MOD-105", "Kapı Kanadı Çarpışma ve Temiz Geçiş Ergonomisi", 1),
    ("MOD-106", "Tefriş–Duvar Yakınlık ve Kullanım Alanı", 1),
    ("MOD-107", "Mekân Oranı ve Dar Kenar Rehberi", 1),
    ("MOD-108", "Islak Hacim Temel Ergonomi ve Kapı Yönü", 1),
    ("MOD-109", "Otomatik İlişki ve Komşuluk Diyagramı", 1),
    ("MOD-110", "Kamusal–Yarı Özel–Özel Alan Kurgusu", 1),
    ("MOD-111", "Sirkülasyon ve Net Kullanım Alanı Verimliliği", 1),
    ("MOD-112", "Yalıtılmış ve Kör Nokta Hacim Tespiti", 1),
    ("MOD-113", "2.5B/3B Prizmatik Kütle ve Doluluk–Boşluk", 1),
    ("MOD-114", "Güneş Yörüngesi ve Gölge Çalışması", 1),
    ("MOD-115", "Doğal Aydınlatma ve Sağır Oda Kontrolü", 1),
    ("MOD-116", "Destekleyici Stüdyo Jürisi", 1),
    ("MOD-117", "Kurucu Usta Mimarlar Merceği", 1),
    ("MOD-118", "Ching ve Neufert Görsel Okuma Kartları", 1),
    ("MOD-201", "Planlı Alanlar İmar Yönetmeliği Piyes İncelemesi", 2),
    ("MOD-202", "Konut İçi Koridor ve Kapı Açıklığı İncelemesi", 2),
    ("MOD-203", "Islak Hacim Şaftı ve Balkon Korkuluk İncelemesi", 2),
    ("MOD-204", "Erişilebilirlik Dönüş Alanı İncelemesi", 2),
    ("MOD-205", "Giriş Rampası Eğim ve Sahanlık İncelemesi", 2),
    ("MOD-206", "Engelsiz WC/Banyo Transfer Alanı", 2),
    ("MOD-207", "Aks Izgarası ve Kolon Sürekliliği", 2),
    ("MOD-208", "Merdiven Geometrisi ve Blondel Hesabı", 2),
    ("MOD-209", "Yangın ve Isı Yalıtımı Öğretici Ön Uyarısı", 2),
    ("MOD-210", "3B Engelsiz Erişim ve İmar Görselleştirme", 2),
    ("MOD-211", "Hiyerarşik Mevzuat RAG Madde Kartları", 2),
    ("MOD-212", "Yapıcı Atölye Kritiği Jürisi", 2),
    ("MOD-213", "Konut, Bağlam ve Tektonik Perspektifleri", 2),
    ("MOD-301", "Yangın Kaçış Yolu Teknik İncelemesi", 3),
    ("MOD-302", "Çıkmaz Koridor ve Darboğaz Adayları", 3),
    ("MOD-303", "Korunumlu Yangın Merdiveni, Hol ve Kapı Yönü", 3),
    ("MOD-304", "Cephe Saydamlık Oranı ve Güneş Kazancı", 3),
    ("MOD-305", "Dış Duvar Yalıtımlı Kesit İncelemesi", 3),
    ("MOD-306", "Geometrik Kompaktlık ve Havalandırma", 3),
    ("MOD-307", "Otopark Yeri Ölçü ve Erişilebilirlik İncelemesi", 3),
    ("MOD-308", "Otopark Rampası ve Manevra Yolu", 3),
    ("MOD-309", "Taşıyıcı Sistem Simetrisi Ön Analizi", 3),
    ("MOD-310", "MEP Şaft ve Islak Hacim Düşey Sürekliliği", 3),
    ("MOD-311", "3B Yangın, İklim ve Statik Kanıt İşaretleri", 3),
    ("MOD-312", "Sığınak Öğretici Ön Değerlendirmesi", 3),
    ("MOD-313", "Teknik Disiplinlerarası Jüri", 3),
    ("MOD-314", "Strüktür ve Performans Perspektifleri", 3),
    ("MOD-401", "Sığınak Kapasite ve Alan İncelemesi", 4),
    ("MOD-402", "Sığınak Kapısı, Duvarı ve İmdat Bacası", 4),
    ("MOD-403", "Parsel Çekme Mesafesi ve TAKS/KAKS", 4),
    ("MOD-404", "Toplanma Alanı ve Tahliye Kapasitesi", 4),
    ("MOD-405", "Mimari–Statik–MEP Çakışma Adayları", 4),
    ("MOD-406", "Mevzuat Kanıt Zinciri İnceleme Paketi", 4),
    ("MOD-407", "Bitirme Jürisi ve İkinci Tur Görüşler", 4),
    ("MOD-408", "Kentsel Ölçek ve Tasarım Yaklaşımları", 4),
    ("MOD-409", "Revizyon Farkı ve Dönemsel Trend", 4),
    ("MOD-410", "Akademik Teknik Ön İnceleme PDF Raporu", 4),
)

MODULES: tuple[CurriculumModule, ...] = tuple(
    CurriculumModule(code, title, grade) for code, title, grade in _CATALOGUE
)
CATALOGUE_VERSION = "0.1-candidate"
GRADE_COUNTS = {1: 18, 2: 31, 3: 45, 4: 55}


def modules_for_grade(grade: int) -> tuple[CurriculumModule, ...]:
    """Return the inherited catalog; never imply executable module readiness."""
    if type(grade) is not int or grade not in GRADE_COUNTS:
        raise ValueError("Project grade must be an integer from 1 to 4")
    return tuple(item for item in MODULES if item.introduced_grade <= grade)


def grade_snapshot(grade: int) -> dict:
    items = modules_for_grade(grade)
    return {
        "schema_version": CATALOGUE_VERSION,
        "grade": grade,
        "catalogued_module_count": len(items),
        "software_modules_accepted": 0,
        "qualification": "CATALOGUE_ONLY_NOT_PRODUCT_ACCEPTANCE",
        "legal_gate": "REGULATORY_LOCKED",
        "modules": [item.as_dict() for item in items],
    }


def validate_catalogue() -> None:
    codes = [m.code for m in MODULES]
    if len(codes) != 55 or len(set(codes)) != 55:
        raise RuntimeError("Curriculum requires 55 unique catalogue IDs")
    for grade, count in GRADE_COUNTS.items():
        if len(modules_for_grade(grade)) != count:
            raise RuntimeError(f"Invalid cumulative catalogue count: grade {grade}")
    if any(m.grading_enabled or m.regulatory_approved for m in MODULES):
        raise RuntimeError("Catalogue data must never grant grading or regulatory approval")


validate_catalogue()
