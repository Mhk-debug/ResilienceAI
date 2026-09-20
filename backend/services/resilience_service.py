import logging
from typing import Optional

from project_schema import (
    BuildingInput,
    ResilienceAssessmentResponse,
    BuildingLLMContext
)

from services.damage_model import DamageModel
from richtor_mappings import decode_building_feature


logger = logging.getLogger(__name__)


def predict_resilience(
    payload: BuildingInput,
    damage_model: DamageModel,
    epi_distance_km: Optional[float] = None
) -> ResilienceAssessmentResponse:
    """
    Runs the damage-model inference pipeline.

    Steps:
    1. Serialise the building input
    2. Build the model's feature frame (app codes -> survey vocabulary, site term)
    3. Run the ordinal damage model (grades 1-5)
    4. Generate the LLM-readable building context, including the damage distribution

    The site term is the epicentral distance to the governing event for the assessment
    location, supplied by the hazard engine. The model is an ordinal cumulative-link
    decomposition: `resilience_score = 100 * (5 - E[grade]) / 4`, so the 0-100 scale and
    its direction are unchanged from the retired three-class artifact.
    """

    raw_input = payload.model_dump()

    # -----------------------------------
    # Run the damage model
    # -----------------------------------

    prediction = damage_model.predict(raw_input, epi_distance_km=epi_distance_km)

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
                ),

            "land_surface_condition":
                raw_input.get(
                    "land_surface_condition"
                ),

            "attached_sides":
                raw_input.get(
                    "position"
                ),

            "plan_configuration":
                raw_input.get(
                    "plan_configuration"
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
                ),

            "floor_above_ground":
                raw_input.get(
                    "other_floor_type"
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
                ),

            "stone_flag":
                bool(
                    raw_input.get(
                        "has_superstructure_stone_flag"
                    )
                ),

            "cement_mortar_stone":
                bool(
                    raw_input.get(
                        "has_superstructure_cement_mortar_stone"
                    )
                ),

            "mud_mortar_brick":
                bool(
                    raw_input.get(
                        "has_superstructure_mud_mortar_brick"
                    )
                ),

            "bamboo":
                bool(
                    raw_input.get(
                        "has_superstructure_bamboo"
                    )
                ),

            "other_material":
                bool(
                    raw_input.get(
                        "has_superstructure_other"
                    )
                )
        },


        # The model's actual output: the full damage distribution, not just a point score.
        # The LLM reasons about severe-damage probability and the confidence spread.
        "damage": {

            "expected_damage_grade":
                prediction["expected_grade"],

            "most_likely_grade":
                prediction["grade_class"],

            "grade_probabilities":
                prediction["probabilities"],

            "severe_damage_probability_grade4_or_5":
                prediction["p_severe_grade45"],

            "resilience_score":
                prediction["resilience_score"],

            "model_version":
                prediction["model_version"]
        }
    }


    building_context = BuildingLLMContext.model_validate(
        context_data
    )


    return ResilienceAssessmentResponse(

        status="success",

        resilience_score=round(
            float(prediction["resilience_score"]),
            2
        ),

        building_llm_context=building_context,

        model_version=prediction["model_version"],

        expected_grade=prediction["expected_grade"],

        grade_class=prediction["grade_class"],

        probabilities=prediction["probabilities"],

        p_severe_grade45=prediction["p_severe_grade45"],

        used_fallback_model=False,

        flags=prediction["flags"]
    )
