"""
scripts/baseline_comparison.py

Compare LLM outputs with and without RAG for representative scenarios.

This script runs the same assessment twice:
1. Without retrieval (baseline — retriever=None)
2. With retrieval (RAG — retriever=build_default_retriever())

Then compares the outputs for specificity, technical accuracy, and quality.

Usage:
    python scripts/baseline_comparison.py

Requires:
    - GEMINI_API_KEY environment variable
    - ChromaDB index built (run scripts/build_kb_index.py first)
    - ML model files in backend/models/
"""

import os
import sys
import json
import time
from pprint import pprint

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from project_schema import (
    BuildingInput,
    HazardInput,
    LLMAnalysisInput,
    EnvironmentalContext,
)
from services.resilience_service import predict_resilience
from services.hazard_engine import calculate_hazard_pydantic
from services.llm_services import create_llm_service
from services.retrieval import build_default_retriever

import joblib
import logging
import asyncio

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Test Scenarios
# ──────────────────────────────────────────────────────────────

SCENARIOS = [
    {
        "name": "A — Mud mortar stone, near Sagaing Fault",
        "input": {
            "latitude": 22.0, "longitude": 96.0,
            "count_floors_pre_eq": 3, "age": 60,
            "area_sq_ft": 800, "height_ft": 24,
            "foundation_type": "r", "roof_type": "n", "ground_floor_type": "f",
            "has_superstructure_mud_mortar_stone": 1,
            "has_superstructure_rc_engineered": 0,
            "has_superstructure_cement_mortar_brick": 0,
            "has_superstructure_rc_non_engineered": 0,
            "has_superstructure_adobe_mud": 0,
            "has_superstructure_timber": 0,
        },
    },
    {
        "name": "B — RC engineered, Yangon",
        "input": {
            "latitude": 16.8, "longitude": 96.1,
            "count_floors_pre_eq": 2, "age": 10,
            "area_sq_ft": 1500, "height_ft": 20,
            "foundation_type": "i", "roof_type": "x", "ground_floor_type": "x",
            "has_superstructure_mud_mortar_stone": 0,
            "has_superstructure_rc_engineered": 1,
            "has_superstructure_cement_mortar_brick": 0,
            "has_superstructure_rc_non_engineered": 0,
            "has_superstructure_adobe_mud": 0,
            "has_superstructure_timber": 0,
        },
    },
    {
        "name": "C — Cement brick, Mandalay",
        "input": {
            "latitude": 21.9, "longitude": 96.1,
            "count_floors_pre_eq": 5, "age": 30,
            "area_sq_ft": 1200, "height_ft": 45,
            "foundation_type": "u", "roof_type": "q", "ground_floor_type": "v",
            "has_superstructure_mud_mortar_stone": 0,
            "has_superstructure_rc_engineered": 0,
            "has_superstructure_cement_mortar_brick": 1,
            "has_superstructure_rc_non_engineered": 0,
            "has_superstructure_adobe_mud": 0,
            "has_superstructure_timber": 0,
        },
    },
]


def load_model():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "..", "models", "seismic_resilience_xgb.pkl")
    schema_path = os.path.join(base_dir, "..", "models", "model_features.json")
    model = joblib.load(model_path)
    with open(schema_path, "r") as f:
        expected_features = json.load(f)
    return model, expected_features


def run_assessment(raw_input, model, expected_features, llm_service):
    """Run the full pipeline and return LLM output + timing."""
    building_input = BuildingInput(**raw_input)
    resilience_result = predict_resilience(
        payload=building_input, model=model, expected_features=expected_features,
    )

    hazard_input = HazardInput(
        latitude=raw_input["latitude"], longitude=raw_input["longitude"],
        search_radius_km=100, historical_years=50, minimum_magnitude=4.5,
    )
    hazard_result = asyncio.run(calculate_hazard_pydantic(hazard_input))
    env_ctx = EnvironmentalContext(**hazard_result.environmental_context)

    llm_input = LLMAnalysisInput(
        building_context=resilience_result.building_llm_context,
        environmental_context=env_ctx,
    )

    t0 = time.time()
    llm_result = llm_service.analyze(llm_input)
    elapsed = time.time() - t0

    return {
        "resilience_score": resilience_result.resilience_score,
        "hazard_score": env_ctx.hazard_score,
        "hazard_level": env_ctx.hazard_level,
        "llm": llm_result,
        "time": elapsed,
    }


def compare_outputs(baseline, rag, scenario_name):
    """Compare baseline vs RAG outputs and print analysis."""
    print(f"\n{'='*70}")
    print(f"COMPARISON: {scenario_name}")
    print(f"{'='*70}")

    bl = baseline["llm"]
    rag_result = rag["llm"]

    # Compare summary items
    print(f"\n  SUMMARY COMPARISON:")
    print(f"  {'#':<3} {'BASELINE':<50} {'RAG':<50}")
    print(f"  {'-'*103}")
    for i in range(6):
        b = bl.summary[i] if i < len(bl.summary) else ""
        r = rag_result.summary[i] if i < len(rag_result.summary) else ""
        print(f"  {i+1:<3} {b:<50} {r:<50}")

    # Compare recommendations
    print(f"\n  RECOMMENDATIONS COMPARISON:")
    for i in range(5):
        b = bl.recommendations[i] if i < len(bl.recommendations) else None
        r = rag_result.recommendations[i] if i < len(rag_result.recommendations) else None
        if b and r:
            print(f"\n    #{i+1} [{b.priority}] {b.title}")
            print(f"      Baseline: {b.description}")
            print(f"      RAG:      [{r.priority}] {r.title}")
            print(f"                {r.description}")

    # Compare risk interpretation
    print(f"\n  RISK INTERPRETATION:")
    b_ri = bl.risk_interpretation
    r_ri = rag_result.risk_interpretation
    print(f"    Structural:")
    print(f"      Baseline: {b_ri.structural_assessment}")
    print(f"      RAG:      {r_ri.structural_assessment}")
    print(f"    Environmental:")
    print(f"      Baseline: {b_ri.environmental_assessment}")
    print(f"      RAG:      {r_ri.environmental_assessment}")
    print(f"    Overall:")
    print(f"      Baseline: {b_ri.overall_reasoning}")
    print(f"      RAG:      {r_ri.overall_reasoning}")

    # Timing comparison
    print(f"\n  TIMING:")
    print(f"    Baseline LLM: {baseline['time']:.2f}s")
    print(f"    RAG LLM:      {rag['time']:.2f}s")
    print(f"    Difference:   {rag['time'] - baseline['time']:+.2f}s")

    # Qualitative assessment
    print(f"\n  QUALITATIVE NOTES:")
    print(f"    Confidence: Baseline={bl.confidence:.2f}, RAG={rag_result.confidence:.2f}")

    # Check for specific terms that indicate RAG grounding
    rag_text = str(rag_result.model_dump()).lower()
    baseline_text = str(bl.model_dump()).lower()
    rag_specific_terms = ["sagaing", "fema", "usgs", "site class", "liquefaction",
                          "out-of-plane", "soft story", "retrofit"]
    for term in rag_specific_terms:
        in_rag = term in rag_text
        in_baseline = term in baseline_text
        if in_rag and not in_baseline:
            print(f"    ✓ RAG uniquely mentions '{term}'")
        elif in_rag and in_baseline:
            pass  # Both mention it — not notable
        elif not in_rag and in_baseline:
            print(f"    ⚠ Baseline uniquely mentions '{term}'")


def main():
    print("=" * 70)
    print("RESILIENCEAI — BASELINE vs RAG COMPARISON")
    print("=" * 70)

    model, expected_features = load_model()
    retriever = build_default_retriever()

    if retriever is None:
        print("\n⚠  Retriever not available. Build the index first:")
        print("   python scripts/build_kb_index.py\n")
        return

    # Create two services: one without RAG, one with
    baseline_service = create_llm_service(retriever=None)
    rag_service = create_llm_service(retriever=retriever)

    for scenario in SCENARIOS:
        print(f"\n{'#'*70}")
        print(f"# Running: {scenario['name']}")
        print(f"{'#'*70}")

        # Run baseline (no RAG)
        print("\n  → Running baseline (no RAG)...")
        baseline = run_assessment(
            scenario["input"], model, expected_features, baseline_service
        )

        # Run RAG
        print("  → Running RAG...")
        rag = run_assessment(
            scenario["input"], model, expected_features, rag_service
        )

        # Compare
        compare_outputs(baseline, rag, scenario["name"])

    print("\n" + "=" * 70)
    print("COMPARISON COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()