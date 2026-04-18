"""
Industrial AI core — re-exports the 4-layer pipeline from api/_pipeline.py.

Thin wrapper so this demo has the same shape as the others. The source of
truth is api/_pipeline.py (shared with the Vercel handlers api/detect.py,
api/predict.py, api/diagnose.py, api/run.py).
"""
from __future__ import annotations

import os
import sys

# Pull from api/_pipeline.py — repo root is two levels up from this file.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_API_DIR = os.path.join(_REPO_ROOT, "api")
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)

from _pipeline import (  # noqa: E402  (re-exports)
    PerceptionLayer,
    PredictionLayer,
    OntologyLayer,
    DiagnosisLayer,
    run_pipeline,
    generate_test_data,
    DATASETS,
    DEFAULT_DATASET,
)

__all__ = [
    "PerceptionLayer",
    "PredictionLayer",
    "OntologyLayer",
    "DiagnosisLayer",
    "run_pipeline",
    "generate_test_data",
    "DATASETS",
    "DEFAULT_DATASET",
]
