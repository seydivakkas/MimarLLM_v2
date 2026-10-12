"""RapidOCR CPU adapter. Optional and never calls a remote OCR service."""
from __future__ import annotations

from importlib import metadata

from mimarllm.core.models import TextCandidate
from mimarllm.importers.pdf import RenderedRegion


class OcrUnavailable(RuntimeError):
    """OCR runtime or required CPU implementation unavailable."""


class RapidCpuOcr:
    def __init__(self) -> None:
        try:
            metadata.version("onnxruntime")
            try:
                metadata.version("onnxruntime-gpu")
            except metadata.PackageNotFoundError:
                pass
            else:
                raise OcrUnavailable("GPU ONNX Runtime installed; use CPU-only onnxruntime wheel")
            import onnxruntime as ort
            if "CPUExecutionProvider" not in ort.get_available_providers():
                raise OcrUnavailable("CPUExecutionProvider missing")
            from rapidocr import RapidOCR, EngineType
        except OcrUnavailable:
            raise
        except (ImportError, metadata.PackageNotFoundError) as exc:
            raise OcrUnavailable("Install optional local packages: rapidocr onnxruntime") from exc
        # Force the local ONNX Runtime backend; only the CPU runtime wheel is allowed.
        self._engine = RapidOCR(params={
            "Det.engine_type": EngineType.ONNXRUNTIME,
            "Cls.engine_type": EngineType.ONNXRUNTIME,
            "Rec.engine_type": EngineType.ONNXRUNTIME,
        })

    def read(self, region: RenderedRegion) -> list[TextCandidate]:
        from PIL import Image
        if not isinstance(region.image, Image.Image):
            raise TypeError("RenderedRegion.image must be a PIL image")
        response = self._engine(region.image)
        if response.boxes is None or response.txts is None:
            return []
        boxes, texts = response.boxes, response.txts
        scores = response.scores
        if scores is None:
            raise ValueError("OCR recognition returned no scores")
        if len(boxes) != len(texts) or len(scores) != len(texts):
            raise ValueError("OCR result arrays have different sizes")
        candidates = []
        for idx, (polygon, text, score) in enumerate(zip(boxes, texts, scores)):
            if len(polygon) != 4:
                raise ValueError("OCR text polygon must contain exactly four points")
            points = tuple(region.pixel_to_source(float(p[0]), float(p[1])) for p in polygon)
            candidates.append(TextCandidate(
                candidate_id=f"p{region.page_index}-ocr{idx}",
                page_index=region.page_index, text=str(text),
                method="rapidocr_cpu", polygon=points, confidence=float(score),
                review_required=True,
            ))
        return candidates
