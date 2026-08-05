"""
scripts/validate_pipeline.py

End-to-end validation script for the assessment pipeline.

Runs the complete pipeline (ML → Hazard → Retrieval → LLM) for
representative building scenarios and records every stage's output.

Usage:
    python scripts/validate_pipeline.py

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

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from project_schema import (
    BuildingInput,
    HazardInput,
    LLMAnalysisInput,
    BuildingLLMContext,
    EnvironmentalContext,
)
from services.pipeline import process_and_align_inference_data
from services.resilience_engine import calculate_resilience_score
from services.resilience_service import predict_resilience
from services.hazard_engine import calculate_hazard_pydantic
from services.llm_services import create_llm_service
from services.retrieval import build_default_retriever
from richtor_mappings import decode_building_feature

import joblib
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Test Scenarios
# ──────────────────────────────────────────────────────────────

SCENARIOS = [
    {
        "name": "A — Mud mortar stone, near Sagaing Fault",
        "input": {
            "latitude": 22.0,
            "longitude": 96.0,
            "count_floors_pre_eq": 3,
            "age": 60,
            "area_sq_ft": 800,
            "height_ft": 24,
            "foundation_type": "r",  # Mud-Stone
            "roof_type": "n",        # Bamboo/Timber
            "ground_floor_type": "f", # Mud floor
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
            "latitude": 16.8,
            "longitude": 96.1,
            "count_floors_pre_eq": 2,
            "age": 10,
            "area_sq_ft": 1500,
            "height_ft": 20,
            "foundation_type": "i",  # Reinforced Concrete
            "roof_type": "x",        # RC slab
            "ground_floor_type": "x", # RC floor
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
            "latitude": 21.9,
            "longitude": 96.1,
            "count_floors_pre_eq": 5,
            "age": 30,
            "area_sq_ft": 1200,
            "height_ft": 45,
            "foundation_type": "u",  # Cement-Stone Masonry
            "roof_type": "q",        # Corrugated Metal
            "ground_floor_type": "v", # Brick/Stone floor
            "has_superstructure_mud_mortar_stone": 0,
            "has_superstructure_rc_engineered": 0,
            "has_superstructure_cement_mortar_brick": 1,
            "has_superstructure_rc_non_engineered": 0,
            "has_superstructure_adobe_mud": 0,
            "has_superstructure_timber": 0,
        },
    },
]


# ──────────────────────────────────────────────────────────────
# Validation Runner
# ──────────────────────────────────────────────────────────────


def load_model():
    """Load the ML model and feature schema."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "..", "models", "seismic_resilience_xgb.pkl")
    schema_path = os.path.join(base_dir, "..", "models", "model_features.json")

    if not os.path.exists(model_path) or not os.path.exists(schema_path):
        logger.error("Model files not found. Run from backend/ directory.")
        sys.exit(1)

    model = joblib.load(model_path)
    with open(schema_path, "r") as f:
        expected_features = json.load(f)

    logger.info("Model loaded: %s (%d features)", model_path, len(expected_features))
    return model, expected_features


def run_scenario(name: str, raw_input: dict, model, expected_features, llm_service):
    """Run the full pipeline for one scenario and print results."""
    print("\n" + "=" * 70)
    print(f"SCENARIO: {name}")
    print("=" * 70)

    # ── Stage 1: ML Prediction ──
    print("\n--- STAGE 1: ML Resilience Prediction ---")
    t0 = time.time()

    building_input = BuildingInput(**raw_input)
    resilience_result = predict_resilience(
        payload=building_input,
        model=model,
        expected_features=expected_features,
    )
    ml_elapsed = time.time() - t0
    print(f"  Resilience Score: {resilience_result.resilience_score:.2f}/100")
    print(f"  Status: {resilience_result.status}")
    print(f"  Time: {ml_elapsed:.2f}s")

    # ── Stage 2: Hazard Engine ──
    print("\n--- STAGE 2: Hazard Engine ---")
    t0 = time.time()

    import asyncio
    hazard_input = HazardInput(
        latitude=raw_input["latitude"],
        longitude=raw_input["longitude"],
        search_radius_km=100,
        historical_years=50,
        minimum_magnitude=4.5,
    )
    hazard_result = asyncio.run(calculate_hazard_pydantic(hazard_input))
    hazard_elapsed = time.time() - t0
    env_ctx = hazard_result.environmental_context
    print(f"  Hazard Score: {env_ctx['hazard_score']:.1f}/100")
    print(f"  Hazard Level: {env_ctx['hazard_level']}")
    print(f"  Fault Distance: {env_ctx['faults']['distance_km']:.1f} km")
    print(f"  Soil Class: {env_ctx['soil']['classification']}")
    print(f"  Time: {hazard_elapsed:.2f}s")

    # ── Stage 3: Knowledge Retrieval ──
    print("\n--- STAGE 3: Knowledge Retrieval ---")
    t0 = time.time()

    building_ctx = resilience_result.building_llm_context
    env_ctx_obj = EnvironmentalContext(**env_ctx)

    results = []
    if llm_service.retriever is not None:
        results = llm_service.retriever.retrieve(building_ctx, env_ctx_obj)
        retrieval_elapsed = time.time() - t0
        print(f"  Retrieved {len(results)} chunks in {retrieval_elapsed*1000:.0f} ms")
        for r in results:
            print(f"    [{r.channel}] {r.metadata.get('title', 'Untitled')} "
                  f"(score={r.score:.3f})")
    else:
        retrieval_elapsed = 0
        print("  Retriever not available (no index)")

    # ── Stage 4: LLM Analysis ──
    print("\n--- STAGE 4: LLM Analysis ---")
    t0 = time.time()

    llm_input = LLMAnalysisInput(
        building_context=building_ctx,
        environmental_context=env_ctx_obj,
    )
    llm_result = llm_service.analyze(llm_input)
    llm_elapsed = time.time() - t0
    print(f"  Time: {llm_elapsed:.2f}s")
    print(f"  Confidence: {llm_result.confidence:.2f}")
    print(f"  Summary items: {len(llm_result.summary)}")
    print(f"  Recommendations: {len(llm_result.recommendations)}")

    # Print summary
    print("\n  Summary:")
    for i, item in enumerate(llm_result.summary, 1):
        print(f"    {i}. {item}")

    print("\n  Recommendations:")
    for i, rec in enumerate(llm_result.recommendations, 1):
        print(f"    {i}. [{rec.priority}] {rec.title}")
        print(f"       {rec.description}")

    print("\n  Risk Interpretation:")
    ri = llm_result.risk_interpretation
    print(f"    Structural: {ri.structural_assessment}")
    print(f"    Environmental: {ri.environmental_assessment}")
    print(f"    Overall: {ri.overall_reasoning}")

    # ── Summary ──
    total = ml_elapsed + hazard_elapsed + retrieval_elapsed + llm_elapsed
    print(f"\n  Total pipeline time: {total:.2f}s")
    print(f"    ML: {ml_elapsed:.2f}s | Hazard: {hazard_elapsed:.2f}s | "
          f"Retrieval: {retrieval_elapsed*1000:.0f}ms | LLM: {llm_elapsed:.2f}s")

    return {
        "scenario": name,
        "resilience_score": resilience_result.resilience_score,
        "hazard_score": env_ctx["hazard_score"],
        "hazard_level": env_ctx["hazard_level"],
        "retrieved_chunks": len(results) if llm_service.retriever is not None else 0,
        "total_time": total,
    }


def main():
    print("=" * 70)
    print("RESILIENCEAI — PIPELINE VALIDATION")
    print("=" * 70)

    # Load model
    model, expected_features = load_model()

    # Initialize retriever (may be None)
    retriever = build_default_retriever()
    llm_service = create_llm_service(retriever=retriever)

    if retriever is None:
        print("\n⚠  Retriever not available. LLM will run without RAG context.")
        print("   Run `python scripts/build_kb_index.py` to build the index.\n")

    # Run each scenario
    results = []
    for scenario in SCENARIOS:
        result = run_scenario(
            name=scenario["name"],
            raw_input=scenario["input"],
            model=model,
            expected_features=expected_features,
            llm_service=llm_service,
        )
        results.append(result)

    # Summary table
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"{'Scenario':<40} {'Resilience':<12} {'Hazard':<10} {'Chunks':<8} {'LLM Conf':<10} {'Time':<8}")
    print("-" * 70)
    for r in results:
        print(f"{r['scenario']:<40} {r['resilience_score']:<12.2f} "
              f"{r['hazard_score']:<10.1f} {r['retrieved_chunks']:<8} "
              f"{r['llm_confidence']:<10.2f} {r['total_time']:<8.2f}")


if __name__ == "__main__":
    main()