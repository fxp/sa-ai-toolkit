"""Tests for Industrial AI 4-layer pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import (  # noqa: E402
    PerceptionLayer, PredictionLayer, OntologyLayer, DiagnosisLayer, run_pipeline,
)


def test_perception_visual_shape():
    v = PerceptionLayer.detect_visual(text_prompt="defect")
    assert v["model"] == "SAM3"
    assert "detections" in v
    assert isinstance(v["detections"], list)
    assert v["num_detections"] == len(v["detections"])


def test_perception_audio_shape():
    a = PerceptionLayer.detect_audio()
    assert a["model"] == "SAM-Audio"
    assert "anomalies" in a


def test_prediction_forecast_shape():
    y = PredictionLayer.forecast(None, 72, "良率(%)")
    assert y["horizon"] == 72
    assert len(y["point_forecast"]) == 72
    assert set(y["quantiles"].keys()) == {"q10", "q50", "q90"}


def test_ontology_trace_shape():
    o = OntologyLayer.trace_root_cause("划痕")
    assert "traces" in o
    assert isinstance(o["traces"], list)


def test_diagnosis_shape():
    v = PerceptionLayer.detect_visual()
    a = PerceptionLayer.detect_audio()
    p = PredictionLayer.predict_equipment_rul()
    o = OntologyLayer.trace_root_cause("划痕")
    d = DiagnosisLayer.diagnose(v, p, o, a, use_llm=False)
    assert "root_causes" in d
    assert "summary" in d


def test_run_pipeline_completes():
    report = run_pipeline(use_llm=False, verbose=False)
    assert "perception" in report
    assert "prediction" in report
    assert "ontology" in report
    assert "diagnosis" in report
