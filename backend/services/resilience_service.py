import logging

from schema import (
    BuildingInput,
    ResilienceAssessmentResponse,
    BuildingLLMContext
)

from services.pipeline import (
    process_and_align_inference_data
)

from services.resilience_engine import (
    calculate_resilience_score
)

from richtor_mappings import decode_building_feature


logger = logging.getLogger(__name__)


def predict_resilience(
    payload: BuildingInput,
    model,
    expected_features
) -> ResilienceAssessmentResponse:
    """
    Runs the complete resilience ML inference pipeline.

    Steps:
    1. Convert input to dictionary
    2. Align features with training schema
    3. Run XGBoost prediction
    4. Generate LLM-readable building context
    """

    raw_input = payload.model_dump()


    # -----------------------------------
    # Prepare ML input
    # -----------------------------------

    dataframe = process_and_align_inference_data(
        raw_input_dict=raw_input,
        trained_model=model,
        expected_features_list=expected_features
    )


    # -----------------------------------
    # Predict resilience score
    # -----------------------------------

    score = calculate_resilience_score(
        model,
        dataframe
    )


    # -----------------------------------
    # Create LLM context
    # -----------------------------------

    context_data = {

        "structural": {

            "floors":
                raw_input.get(
                    "count_floors_pre_eq"
                ),

            "age_years":
                raw_input.get(
                    "age"
                ),

            "floor_area_sq_feets":
                raw_input.get(
                    "area_sq_ft"
                ),

            "height_feets":
                raw_input.get(
                    "height_ft"
                )
        },


        "material": {

            "roof_type":
                decode_building_feature(
                    "roof_type",
                    str(
                        raw_input.get(
                            "roof_type",
                            ""
                        )
                    )
                ),

            "foundation_type":
                decode_building_feature(
                    "foundation_type",
                    str(
                        raw_input.get(
                            "foundation_type",
                            ""
                        )
                    )
                ),

            "ground_floor_type":
                decode_building_feature(
                    "ground_floor_type",
                    str(
                        raw_input.get(
                            "ground_floor_type",
                            ""
                        )
                    )
                )
        },


        "substructure": {

            "mud_mortar_stone":
                bool(
                    raw_input.get(
                        "has_superstructure_mud_mortar_stone"
                    )
                ),

            "cement_brick":
                bool(
                    raw_input.get(
                        "has_superstructure_cement_mortar_brick"
                    )
                ),

            "rc_engineered":
                bool(
                    raw_input.get(
                        "has_superstructure_rc_engineered"
                    )
                ),

            "rc_non_engineered":
                bool(
                    raw_input.get(
                        "has_superstructure_rc_non_engineered"
                    )
                ),

            "adobe_mud":
                bool(
                    raw_input.get(
                        "has_superstructure_adobe_mud"
                    )
                ),

            "timber":
                bool(
                    raw_input.get(
                        "has_superstructure_timber"
                    )
                )
        }
    }


    building_context = BuildingLLMContext.model_validate(
        context_data
    )


    return ResilienceAssessmentResponse(

        status="success",

        resilience_score=round(
            float(score),
            2
        ),

        building_llm_context=building_context
    )