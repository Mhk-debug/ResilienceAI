import os
import json
import time
import random
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
import certifi

from project_schema import (
    BuildingLLMContext,
    EnvironmentalContext,
    LLMAnalysisInput,
    LLMAnalysisOutput,
)

# =========================================================
# ENV SETUP
# =========================================================

os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv()


# =========================================================
# UTIL: SAFE JSON PARSER
# =========================================================

def safe_json_load(text: str) -> Dict[str, Any]:
    """
    Robust JSON parser with fallback extraction.
    Handles extra text or malformed model output.
    """
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("Model did not return valid JSON")

        return json.loads(text[start:end])


# =========================================================
# UTIL: CLEAN GEMINI SCHEMA
# =========================================================

def clean_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep-clean schema for Gemini compatibility.
    Removes unsupported OpenAPI extensions like additionalProperties.
    """
    schema = json.loads(json.dumps(schema))  # deep copy

    def _clean(obj):
        if isinstance(obj, dict):
            obj.pop("additionalProperties", None)

            for v in obj.values():
                _clean(v)

        elif isinstance(obj, list):
            for item in obj:
                _clean(item)

    _clean(schema)
    return schema


# =========================================================
# GENAI CLIENT
# =========================================================

class GenAIClient:
    def __init__(self, model: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.model = model

    def generate(
        self,
        prompt: str,
        schema: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:

        schema = clean_schema(schema)

        retryable_errors = (RuntimeError, TimeoutError)

        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=0.1,
                    ),
                )

                # Robust extraction
                raw_text = getattr(response, "text", None)

                if not raw_text:
                    candidates = getattr(response, "candidates", None)
                    if candidates:
                        first_candidate = candidates[0]
                        content = getattr(first_candidate, "content", None)
                        parts = getattr(content, "parts", None)
                        if parts:
                            first_part = parts[0]
                            raw_text = getattr(first_part, "text", None)

                if not raw_text:
                    raise ValueError("Empty response from Gemini")

                return safe_json_load(raw_text)

            except Exception as e:
                last_error = e

                # retry only transient failures
                if not isinstance(e, retryable_errors):
                    raise RuntimeError(f"Non-retryable error: {e}") from e

                sleep_time = (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(sleep_time)

        raise RuntimeError(
            f"Gemini failed after {max_retries} retries: {last_error}"
        )


# =========================================================
# LLM SERVICE
# =========================================================

class LLMService:
    def __init__(self, client: GenAIClient):
        self.client = client

    def analyze(self, input_data: LLMAnalysisInput) -> LLMAnalysisOutput:
        prompt = self._build_prompt(
            building=input_data.building_context,
            env=input_data.environmental_context,
        )

        schema = LLMAnalysisOutput.model_json_schema()

        result = self.client.generate(prompt, schema=schema)

        return LLMAnalysisOutput(**result)

    # -----------------------------------------------------
    # PROMPT ENGINE
    # -----------------------------------------------------
    def _build_prompt(
        self,
        building: BuildingLLMContext,
        env: EnvironmentalContext
    ) -> str:

        return f"""
You are a seismic risk engineering AI assistant.

Your task is to analyze building structural vulnerability and environmental seismic hazard,
then return a structured JSON response.

You MUST follow the output format exactly and return ONLY valid JSON.
Do not include any explanations outside the JSON.

-----------------------------
BUILDING CONTEXT:
{building.model_dump()}

-----------------------------
ENVIRONMENTAL CONTEXT:
{env.model_dump()}

-----------------------------

OUTPUT REQUIREMENTS:

1. "summary" MUST contain EXACTLY 6 short bullet-point strings representing the
   most important key findings from the assessment.

2. "recommendations" MUST contain EXACTLY 5 actionable engineering or safety recommendations.

3. Each recommendation MUST include:
   - priority: exactly one of "red", "orange", "yellow", or "green"
   - title: a short, clear label
   - description: detailed and actionable guidance

4. "risk_interpretation" MUST provide structured reasoning for:
   - structural assessment
   - environmental assessment
   - overall reasoning
   
-----------------------------
OUTPUT FORMAT (STRICT JSON):

{{
  "summary": [
    "Key finding 1",
    "Key finding 2",
    "Key finding 3",
    "Key finding 4",
    "Key finding 5",
    "Key finding 6"
  ],
  "recommendations": [
    {{
      "priority": "red",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance"
    }},
    {{
      "priority": "orange",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance"
    }},
    {{
      "priority": "yellow",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance"
    }},
    {{
      "priority": "yellow",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance"
    }},
    {{
      "priority": "green",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance"
    }}
  ],
  "risk_interpretation": {{
    "structural_assessment": "Structured reasoning about the building's structural vulnerability",
    "environmental_assessment": "Structured reasoning about environmental seismic hazards",
    "overall_reasoning": "Integrated reasoning explaining the overall risk assessment"
  }},
}}

STRICT RULES:
- Output ONLY valid JSON. Do not include markdown, code fences, or commentary.
- "summary" MUST contain EXACTLY 6 items. No more and no fewer.
- "recommendations" MUST contain EXACTLY 5 items. No more and no fewer.
- Every recommendation MUST include a valid priority, title, and description.
- Recommendations MUST be specific, actionable, and relevant to the assessed building and environmental conditions.
- Do not invent unsupported structural or environmental facts.
- Keep the 6 key findings concise and engineering-focused.
- Ensure consistency between the key findings, risk interpretation, and recommendations.
- The priority should reflect urgency:
  - "red": immediate or critical action
  - "orange": high-priority action
  - "yellow": moderate-priority improvement
  - "green": lower-priority preparedness or maintenance action
"""


# =========================================================
# FACTORY
# =========================================================

def create_llm_service(model: str = "gemini-2.5-flash") -> LLMService:
    client = GenAIClient(model=model)
    return LLMService(client=client)