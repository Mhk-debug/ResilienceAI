# =========================================================
# LIVE INTEGRATION TEST WITH MOCK DATA
# =========================================================

from schema import BuildingLLMContext, EnvironmentalContext, LLMAnalysisInput, LLMAnalysisOutput, LLMFaultContext, LLMGroundMotionContext, LLMHistoricalActivity, LLMSoilContext
from services.llm_services import create_llm_service


if __name__ == "__main__":
    import os
    from pprint import pprint

    print("=" * 60)
    print("RUNNING LIVE LLM SEISMIC ANALYSIS INTEGRATION TEST")
    print("=" * 60)

    # 1. Build precise mock structures matching your updated schema types
    mock_building = BuildingLLMContext(
        structural={
            "system_type": "Non-ductile concrete moment frame",
            "number_of_stories": 6,
            "year_built": 1972,
            "has_soft_story": True
        },
        material={
            "primary_material": "Reinforced Concrete",
            "concrete_strength_psi": 3000,
            "rebar_grade": "Grade 40 (historical/low ductility)"
        },
        substructure={
            "foundation_type": "Shallow spread footings",
            "basement_levels": 0,
            "tie_beams_present": False
        }
    )

    mock_env = EnvironmentalContext(
        hazard_score=78.5,
        hazard_level="High",
        historical_activity=LLMHistoricalActivity(
            classification="Seismically Active Area",
            events_within_radius=14,
            largest_magnitude=6.9
        ),
        faults=LLMFaultContext(
            distance_km=4.2,
            classification="Major Active Strike-Slip"
        ),
        soil=LLMSoilContext(
            classification="Site Class E",
            dominant_soil="Soft clay prone to amplification and liquefaction"
        ),
        ground_motion=LLMGroundMotionContext(
            estimated_mmi=8.0,
            estimated_pga_g=0.48,
            confidence=0.85
        ),
        summary=[
            "Site is situated 4.2 km from a major active fault boundary.",
            "Foundation rests on Class E soft clay which amplifies peak ground acceleration.",
            "Historical activity catalogs multiple local magnitude 6+ events within a 50 km radius."
        ]
    )

    # 2. Package everything into the main input model expected by LLMService.analyze()
    test_input = LLMAnalysisInput(
        building_context=mock_building,
        environmental_context=mock_env
    )

    # 3. Initialize the service using your factory function
    # Adjust model name depending on your chosen API provider (e.g., "gemini-2.5-flash" or "gpt-4o-mini")
    TARGET_MODEL = "gemini-2.5-flash"
    
    print(f"Initializing LLMService with model: {TARGET_MODEL}...")
    service = create_llm_service(model=TARGET_MODEL)

    # 4. Fire the live request and display the structured output object
    print("\nSending context data to LLM for structural analysis...")
    print("Waiting for response...\n")
    
    try:
        # This executes _build_prompt -> client.generate -> _safe_parse -> LLMAnalysisOutput instantiation
        output: LLMAnalysisOutput = service.analyze(test_input)
        
        print("Success! Parsed Pydantic Output Received:")
        print("-" * 50)
        
        # Pretty-print the structured object dictionary
        pprint(output.model_dump() if hasattr(output, "model_dump") else output.__dict__, indent=2)
        print("-" * 50)
        
    except Exception as error:
        print("\n[TEST FAILED] An error occurred during execution.")
        print(f"Error details: {error}")
        print("\nVerify that:")
        print("1. Your API key environment variable (OPENAI_API_KEY or GEMINI_API_KEY) is exported correctly.")
        print("2. Your LLMAnalysisInput wrapper class uses 'building_context' and 'environmental_context' as its attribute names.")