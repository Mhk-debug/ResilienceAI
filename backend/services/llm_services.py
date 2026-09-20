import os
import json
import time
import random
import logging
from typing import Dict, Any, Optional, List, Tuple, Set

from dotenv import load_dotenv
from google import genai
from google.genai import types
import certifi

from project_schema import (
    BuildingLLMContext,
    EnvironmentalContext,
    LLMAnalysisInput,
    LLMAnalysisOutput,
    EvidenceCitation,
)

logger = logging.getLogger(__name__)

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
        # Resolve the key from explicit arg, GEMINI_API_KEY, or GOOGLE_API_KEY.
        # If none is present, the client is left unset and generate() raises a
        # clear, actionable error — the app must still boot without an AI key.
        key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=key) if key else None
        self.model = model
        self._missing_key = not key

    def generate(
        self,
        prompt: str,
        schema: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:

        if self.client is None:
            raise RuntimeError(
                "Gemini API key is not configured. "
                "Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your .env file."
            )

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
    def __init__(
        self,
        client: GenAIClient,
        retriever: Optional[Any] = None,
    ):
        """
        Args:
            client: GenAIClient instance for LLM calls.
            retriever: Optional Retriever instance for knowledge retrieval.
                       If None, retrieval is skipped gracefully.
        """
        self.client = client
        self.retriever = retriever
        self._last_retrieval_ms: float = 0.0
        # Store raw retrieval results for evidence_map construction
        self._last_retrieval_results: List[Any] = []

    # -----------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------

    def analyze(self, input_data: LLMAnalysisInput) -> Tuple[LLMAnalysisOutput, Dict[str, EvidenceCitation]]:
        """
        Analyze the building and environmental context using LLM + RAG.

        Returns:
            Tuple of (LLMAnalysisOutput, evidence_map) where evidence_map
            is a dict of chunk_id -> EvidenceCitation for validated retrieved chunks.
            evidence_map is empty if no RAG results were available.
        """
        start_total = time.time()

        # Attempt knowledge retrieval (fail-safe)
        retrieved_knowledge, retrieved_results = self._retrieve_knowledge(
            building=input_data.building_context,
            env=input_data.environmental_context,
        )

        # Store raw results for evidence_map construction
        self._last_retrieval_results = retrieved_results

        prompt = self._build_prompt(
            building=input_data.building_context,
            env=input_data.environmental_context,
            retrieved_knowledge=retrieved_knowledge,
        )

        prompt_token_estimate = len(prompt.split())

        schema = LLMAnalysisOutput.model_json_schema()

        start_llm = time.time()
        try:
            result = self.client.generate(prompt, schema=schema)
        except Exception as e:
            # Deterministic fallback: keeps the assessment pipeline working when
            # Gemini is unavailable (no key, region-blocked, network error, quota).
            logger.warning(
                "Gemini API unavailable (%s) — using deterministic fallback analysis.",
                e,
            )
            result = self._build_fallback_analysis(
                building=input_data.building_context,
                env=input_data.environmental_context,
                retrieved_results=retrieved_results,
            )
        llm_elapsed = time.time() - start_llm

        # Build and validate evidence citations
        evidence_map = self._build_evidence_map(
            retrieved_results=retrieved_results,
            llm_result=result,
        )

        total_elapsed = time.time() - start_total

        logger.info(
            "LLM analysis complete | "
            "retrieval=%.0fms | "
            "llm=%.2fs | "
            "total=%.2fs | "
            "prompt_words=%d | "
            "rag=%s | "
            "evidence_chunks=%d",
            self._last_retrieval_ms,
            llm_elapsed,
            total_elapsed,
            prompt_token_estimate,
            "enabled" if retrieved_knowledge else "disabled",
            len(evidence_map),
        )

        return LLMAnalysisOutput(**result), evidence_map

    # -----------------------------------------------------
    # KNOWLEDGE RETRIEVAL
    # -----------------------------------------------------

    def _retrieve_knowledge(
        self,
        building: BuildingLLMContext,
        env: EnvironmentalContext,
    ) -> Tuple[str, List[Any]]:
        """
        Retrieve relevant knowledge chunks and format them for the prompt.

        Returns:
            Tuple of (formatted_knowledge_string, raw_results_list).
            Both are empty if retrieval fails or is unavailable.

        This method is designed to never block the assessment pipeline.
        """
        if self.retriever is None:
            return "", []

        try:
            start = time.time()
            results = self.retriever.retrieve(building, env)
            elapsed_ms = (time.time() - start) * 1000
            self._last_retrieval_ms = elapsed_ms

            if not results:
                logger.info("Knowledge retrieval returned 0 chunks (%.0f ms)", elapsed_ms)
                return "", []

            formatted = self._format_retrieved_knowledge(results)
            self._log_retrieval_summary(results, elapsed_ms)
            return formatted, results

        except Exception as e:
            self._last_retrieval_ms = 0.0
            logger.warning("Knowledge retrieval failed: %s", e, exc_info=True)
            return "", []

    # -----------------------------------------------------
    # FORMAT RETRIEVED KNOWLEDGE
    # -----------------------------------------------------

    @staticmethod
    def _format_retrieved_knowledge(results: List[Any]) -> str:
        """
        Format retrieved knowledge chunks into a clean prompt section.

        Scores are NOT exposed to the LLM — only source/category metadata.
        Each reference includes its chunk_id so the LLM can cite it.
        """
        if not results:
            return ""

        lines = [
            "",
            "Retrieved Knowledge",
            "",
            "The following information comes from the project's engineering knowledge base "
            "and should be treated as supporting reference material.",
            "",
        ]

        for i, result in enumerate(results, start=1):
            chunk_id = result.chunk_id
            category = result.metadata.get("category", "General")
            source_title = result.metadata.get("title", "")
            source_org = result.metadata.get("source_org", "")

            lines.append(f"Reference {i} [chunk_id: {chunk_id}]")
            lines.append(f"Category: {category}")
            if source_title:
                lines.append(f"Title: {source_title}")
            if source_org:
                lines.append(f"Source: {source_org}")
            lines.append("")
            lines.append(result.text.strip())
            lines.append("")

        return "\n".join(lines).strip()

    @staticmethod
    def _log_retrieval_summary(results: List[Any], elapsed_ms: float) -> None:
        """Log a structured summary of retrieved knowledge for debugging."""
        channel_summaries: Dict[str, list] = {}
        for r in results:
            channel = r.channel or "unknown"
            tags = r.metadata.get("tags", "")
            channel_summaries.setdefault(channel, []).append(tags)

        summary_parts = []
        for channel, tag_list in channel_summaries.items():
            tags_str = ", ".join(t for t in tag_list if t)
            summary_parts.append(f"{channel}: {tags_str}")

        logger.info(
            "Retrieved %d knowledge chunks in %.0f ms | %s",
            len(results),
            elapsed_ms,
            " | ".join(summary_parts),
        )

    # -----------------------------------------------------
    # EVIDENCE CITATION
    # -----------------------------------------------------

    @staticmethod
    def _validate_evidence_ids(
        evidence_ids: List[str],
        valid_chunk_ids: Set[str],
    ) -> List[str]:
        """
        Validate evidence chunk IDs against the set of actually retrieved chunks.

        Filters out hallucinated or invalid IDs. Logs a warning for each
        invalid ID encountered.

        Args:
            evidence_ids: IDs returned by the LLM.
            valid_chunk_ids: Set of chunk IDs that were actually retrieved.

        Returns:
            List of valid evidence IDs (subset of valid_chunk_ids).
        """
        if not evidence_ids or not valid_chunk_ids:
            return []

        validated: List[str] = []
        for eid in evidence_ids:
            if eid in valid_chunk_ids:
                validated.append(eid)
            else:
                logger.warning(
                    "LLM returned invalid evidence_id '%s' not in retrieved set. Ignoring.",
                    eid,
                )
        return validated

    @staticmethod
    def _build_evidence_map(
        retrieved_results: List[Any],
        llm_result: Dict[str, Any],
    ) -> Dict[str, EvidenceCitation]:
        """
        Build evidence citation map from retrieved chunks and LLM output.

        Only includes chunks whose IDs were cited by the LLM and validated
        against the retrieved set.

        Args:
            retrieved_results: Raw RetrievalResult objects from the retriever.
            llm_result: Parsed LLM JSON output containing evidence_ids.

        Returns:
            Dict mapping chunk_id -> EvidenceCitation for cited+validated chunks.
        """
        if not retrieved_results:
            return {}

        # Collect all evidence_ids cited by the LLM across summary + recommendations
        cited_ids: Set[str] = set()

        # Extract from summary items
        for item in llm_result.get("summary", []):
            if isinstance(item, dict):
                cited_ids.update(item.get("evidence_ids", []))

        # Extract from recommendations
        for rec in llm_result.get("recommendations", []):
            if isinstance(rec, dict):
                cited_ids.update(rec.get("evidence_ids", []))

        if not cited_ids:
            return {}

        # Build set of valid chunk IDs from retrieved results
        valid_ids: Set[str] = {r.chunk_id for r in retrieved_results}

        # Validate cited IDs against retrieved set
        validated_ids = LLMService._validate_evidence_ids(list(cited_ids), valid_ids)

        if not validated_ids:
            return {}

        # Build chunk_id -> RetrievalResult lookup
        result_map: Dict[str, Any] = {r.chunk_id: r for r in retrieved_results}

        # Construct evidence citations
        evidence_map: Dict[str, EvidenceCitation] = {}
        for chunk_id in validated_ids:
            result = result_map[chunk_id]
            # Truncate excerpt to first 300 chars
            excerpt = result.text.strip()[:300]
            if len(result.text.strip()) > 300:
                excerpt += "..."

            evidence_map[chunk_id] = EvidenceCitation(
                chunk_id=chunk_id,
                source_title=result.metadata.get("title", ""),
                source_org=result.metadata.get("source_org", ""),
                source_url=result.metadata.get("source_url", ""),
                category=result.metadata.get("category", ""),
                excerpt=excerpt,
                relevance_score=result.score,
            )

        return evidence_map

    # -----------------------------------------------------
    # DETERMINISTIC FALLBACK ANALYSIS (no Gemini required)
    # -----------------------------------------------------

    @staticmethod
    def _build_fallback_analysis(
        building: BuildingLLMContext,
        env: EnvironmentalContext,
        retrieved_results: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build a rule-based analysis from the building + environmental context.

        Used when the Gemini API is unavailable (no key, region-blocked,
        network failure, or quota). Produces the same strict schema as the
        LLM: 6 summary items, 5 recommendations, risk_interpretation, and a
        lowered confidence so readers know it is not model-generated.

        When retrieval produced results, the most relevant chunks are attached
        as evidence_ids (category-matched) so the fallback output shows the
        same evidence citations as a Gemini-generated analysis.
        """
        structural = building.structural
        material = building.material
        substructure = building.substructure

        floors = structural.get("floors")
        age = structural.get("age_years")
        floor_area = structural.get("floor_area_sq_feets")
        height = structural.get("height_feets")

        hazard_score = env.hazard_score
        hazard_level = env.hazard_level
        fault_km = env.faults.distance_km
        soil_class = env.soil.classification
        soil_dominant = env.soil.dominant_soil
        events = env.historical_activity.events_within_radius
        largest_mag = env.historical_activity.largest_magnitude

        vulnerable_masonry = bool(
            substructure.get("mud_mortar_stone") or substructure.get("adobe_mud")
        )
        non_engineered = bool(substructure.get("rc_non_engineered"))
        engineered = bool(
            substructure.get("rc_engineered") or substructure.get("cement_brick")
        )
        old_building = bool(age and age > 40)
        soft_soil = "E" in (soil_class or "") or "D" in (soil_class or "")
        near_fault = bool(fault_km is not None and fault_km < 15)

        floor_txt = f"{floors}-storey" if floors else "Multi-storey"
        age_txt = f", {age} years old" if age is not None else ""
        material_txt = "engineered RC/cement-brick" if engineered else (
            "non-engineered RC" if non_engineered else "masonry/adobe"
        )

        summary = [
            {
                "text": (
                    f"The {floor_txt} building{age_txt} uses {material_txt} "
                    f"construction and covers {floor_area} sq ft."
                    if floor_area else
                    f"The {floor_txt} building{age_txt} uses {material_txt} construction."
                ),
                "evidence_ids": [],
            },
            {
                "text": (
                    f"Environmental seismic hazard at this site is "
                    f"{hazard_score:.0f}/100 — {hazard_level}."
                ),
                "evidence_ids": [],
            },
            {
                "text": (
                    f"The nearest major fault lies {fault_km:.1f} km away."
                    if fault_km is not None else
                    "No major mapped fault lies near this site."
                ),
                "evidence_ids": [],
            },
            {
                "text": (
                    f"Soil is {soil_class}; {soil_dominant}."
                    if soil_dominant else f"Soil is {soil_class}."
                ),
                "evidence_ids": [],
            },
            {
                "text": (
                    f"{events} historical events (M4.5+) were recorded nearby; "
                    f"the largest reached M{largest_mag}."
                    if largest_mag is not None else
                    f"{events} historical events (M4.5+) were recorded nearby."
                ),
                "evidence_ids": [],
            },
            {
                "text": (
                    "Overall risk is driven mainly by environmental hazard, "
                    "while the building itself is comparatively resilient."
                    if hazard_score >= 50 and engineered else
                    "Building vulnerability is the dominant risk factor and "
                    "should be addressed first."
                    if vulnerable_masonry or non_engineered else
                    "Overall risk reflects a balance of building condition "
                    "and surrounding seismic hazard."
                ),
                "evidence_ids": [],
            },
        ]

        recommendations: List[Dict[str, Any]] = []

        if hazard_score >= 60 and ((vulnerable_masonry or non_engineered) or age is None):
            recommendations.append({
                "priority": "red",
                "title": "Prioritize seismic retrofit",
                "description": (
                    f"Site hazard is {hazard_level} ({hazard_score:.0f}/100) and "
                    "the structure lacks engineered detailing; engage a structural "
                    "engineer to plan a retrofit."
                ),
                "evidence_ids": [],
            })
        if vulnerable_masonry:
            recommendations.append({
                "priority": "red",
                "title": "Anchor masonry walls",
                "description": (
                    "Unreinforced mud/adobe walls can collapse outward during shaking; "
                    "anchor walls to floors and roof and install bracing."
                ),
                "evidence_ids": [],
            })
        if non_engineered:
            recommendations.append({
                "priority": "orange",
                "title": "Upgrade frame detailing",
                "description": (
                    "Non-engineered RC framing needs improved confinement: add column "
                    "ties, beam-column joint reinforcement, and rebar anchorage."
                ),
                "evidence_ids": [],
            })
        if old_building:
            recommendations.append({
                "priority": "orange",
                "title": "Inspect for degradation",
                "description": (
                    f"At about {age} years old, check for cracking, corrosion, and "
                    "rot in load-bearing elements before the next strong shake."
                ),
                "evidence_ids": [],
            })
        if near_fault:
            recommendations.append({
                "priority": "yellow",
                "title": "Prepare emergency plan",
                "description": (
                    f"The site is only {fault_km:.0f} km from a major fault; rehearse "
                    "drop-cover-hold and keep a household emergency kit."
                ),
                "evidence_ids": [],
            })
        if soft_soil:
            recommendations.append({
                "priority": "yellow",
                "title": "Secure heavy objects",
                "description": (
                    f"{soil_class} soil amplifies shaking; strap furniture and secure "
                    "shelving and ceiling fixtures."
                ),
                "evidence_ids": [],
            })
        if floors and floors >= 5:
            recommendations.append({
                "priority": "orange",
                "title": "Check drift and soft storey",
                "description": (
                    f"At {floors} storeys, verify lateral drift and ground-floor "
                    "stiffness to avoid soft-storey collapse."
                ),
                "evidence_ids": [],
            })

        recommendations.append({
            "priority": "green",
            "title": "Annual maintenance check",
            "description": (
                "Repair cracks and leaks yearly and keep structural elements free "
                "of damp, rot, and termite damage."
            ),
            "evidence_ids": [],
        })

        recommendations = recommendations[:5]
        while len(recommendations) < 5:
            recommendations.append({
                "priority": "green",
                "title": "Maintain preparedness",
                "description": (
                    "Keep a disaster kit, secure water heaters, and review "
                    "evacuation routes with the household."
                ),
                "evidence_ids": [],
            })

        structural_txt = (
            f"The {floor_txt} building is {age or 'of unknown'} years old with a "
            f"{material.get('foundation_type', 'standard')} foundation and "
            f"{material.get('roof_type', 'standard')} roof."
        )
        if vulnerable_masonry:
            structural_txt += (
                " Unreinforced masonry construction is highly vulnerable to "
                "out-of-plane wall failure and should be reinforced."
            )
        elif non_engineered:
            structural_txt += (
                " Non-engineered reinforced concrete lacks ductile detailing."
            )
        elif engineered:
            structural_txt += " Engineered construction generally performs well."
        else:
            structural_txt += " Construction type shows moderate vulnerability."

        env_txt = (
            f"The site reports a hazard score of {hazard_score:.0f}/100 "
            f"({hazard_level})"
        )
        if near_fault:
            env_txt += f" and sits {fault_km:.0f} km from a major fault"
        if soft_soil:
            env_txt += f" on amplifying {soil_class} soils"
        env_txt += "."

        analysis = {
            "summary": summary,
            "recommendations": recommendations,
            "risk_interpretation": {
                "structural_assessment": structural_txt,
                "environmental_assessment": env_txt,
                "overall_reasoning": (
                    f"With {hazard_score:.0f}/100 environmental hazard and a "
                    f"{material_txt} structure, the assessed location warrants "
                    "the prioritized improvements above."
                ),
            },
            "confidence": 0.55,
        }

        # Attach retrieved knowledge as evidence so the citation cards render.
        if retrieved_results:
            LLMService._attach_fallback_evidence(analysis, retrieved_results)

        return analysis

    @staticmethod
    def _attach_fallback_evidence(
        analysis: Dict[str, Any],
        retrieved_results: List[Any],
    ) -> None:
        """Assign retrieved chunk IDs to fallback summary/rec items by category."""
        summary = analysis["summary"]
        recommendations = analysis["recommendations"]

        # Which summary item each knowledge category supports.
        summary_slot = {
            "building_vulnerability": 0,   # building description
            "environmental_hazards": 3,    # soil item
            "earthquake_safety": 4,        # historical-events item
            "local_context": 5,            # overall-risk item
            "mitigation": 5,
        }
        # Substring matched against recommendation titles.
        rec_match = {
            "building_vulnerability": ("anchor", "upgrade", "retrofit", "inspect", "drift"),
            "environmental_hazards": ("secure", "prepare"),
            "earthquake_safety": ("prepare", "emergency", "drift"),
            "mitigation": ("annual", "maintain", "retrofit", "inspect"),
            "local_context": ("prepare", "maintain"),
        }

        def attach(target_list, item_idx, chunk_id):
            if 0 > item_idx or item_idx >= len(target_list):
                return
            ids = target_list[item_idx]["evidence_ids"]
            if chunk_id not in ids:
                ids.append(chunk_id)

        for r in retrieved_results:
            category = (r.metadata or {}).get("category", "")
            # summary slot
            slot = summary_slot.get(category)
            if slot is not None:
                attach(summary, slot, r.chunk_id)
            # recommendation match (a chunk may support one summary AND one rec)
            keywords = rec_match.get(category, ())
            if keywords:
                target = next(
                    (i for i, rc in enumerate(recommendations)
                     if any(k in rc["title"].lower() for k in keywords)),
                    None,
                )
                if target is not None:
                    attach(recommendations, target, r.chunk_id)

    # -----------------------------------------------------
    # PROMPT ENGINE
    # -----------------------------------------------------
    def _build_prompt(
        self,
        building: BuildingLLMContext,
        env: EnvironmentalContext,
        retrieved_knowledge: str = "",
    ) -> str:

        # Build the base prompt parts
        parts = [
            self._system_instructions(),
            self._building_section(building),
            self._environmental_section(env),
        ]

        # Inject retrieved knowledge section if available
        if retrieved_knowledge:
            parts.append(self._knowledge_section(retrieved_knowledge))

        parts.append(self._output_requirements())

        return "\n".join(parts)

    @staticmethod
    def _system_instructions() -> str:
        return """\
You are a seismic risk engineering AI assistant.

Your task is to analyze building structural vulnerability and environmental seismic hazard,
then return a structured JSON response.

You MUST follow the output format exactly and return ONLY valid JSON.
Do not include any explanations outside the JSON.

-----------------------------"""

    @staticmethod
    def _building_section(building: BuildingLLMContext) -> str:
        return f"""\
BUILDING CONTEXT:
{building.model_dump()}

-----------------------------"""

    @staticmethod
    def _environmental_section(env: EnvironmentalContext) -> str:
        return f"""\
ENVIRONMENTAL CONTEXT:
{env.model_dump()}

-----------------------------"""

    @staticmethod
    def _knowledge_section(retrieved_knowledge: str) -> str:
        return f"""\
RETRIEVED KNOWLEDGE:
{retrieved_knowledge}

-----------------------------"""

    @staticmethod
    def _output_requirements() -> str:
        return """\
OUTPUT REQUIREMENTS:

1. "summary" MUST contain EXACTLY 6 summary items representing the
   most important key findings from the assessment.
   Each summary item is an object with:
    - "text": the key finding string (12-20 words maximum).
    - "evidence_ids": list of chunk_id strings from the RETRIEVED KNOWLEDGE section
      that support this finding. Use empty list [] if no retrieved knowledge supports it.
      Only use chunk_ids shown in the references (e.g., "doc1__chunk_0").

2. "recommendations" MUST contain EXACTLY 5 actionable engineering or safety recommendations.

3. Each recommendation MUST include:

    - priority: exactly one of "red", "orange", "yellow", or "green"
    - title:
        - 3-6 words maximum
        - clear action label

    - description:
        - 25-35 words maximum
        - one actionable engineering instruction
        - avoid unnecessary explanation

    - evidence_ids: list of chunk_id strings from the RETRIEVED KNOWLEDGE section
      that support this recommendation. Use empty list [] if no retrieved knowledge
      supports it. Only use chunk_ids shown in the references.

4. "risk_interpretation" MUST provide structured reasoning for:
   - structural assessment
   - environmental assessment
   - overall reasoning

   for each of the risk_interpretation string:
   MAXIMUM WORD COUNT: 35
   MINIMUM WORD COUNT: 25
   
-----------------------------
OUTPUT FORMAT (STRICT JSON):

{
  "summary": [
    {"text": "Key finding one", "evidence_ids": ["doc1__chunk_0"]},
    {"text": "Key finding two", "evidence_ids": []},
    {"text": "Key finding three", "evidence_ids": []},
    {"text": "Key finding four", "evidence_ids": []},
    {"text": "Key finding five", "evidence_ids": []},
    {"text": "Key finding six", "evidence_ids": []}
  ],
  "recommendations": [
    {
      "priority": "red",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance",
      "evidence_ids": ["doc1__chunk_0"]
    },
    {
      "priority": "orange",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance",
      "evidence_ids": []
    },
    {
      "priority": "yellow",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance",
      "evidence_ids": []
    },
    {
      "priority": "yellow",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance",
      "evidence_ids": []
    },
    {
      "priority": "green",
      "title": "Recommendation title",
      "description": "Detailed actionable engineering or safety guidance",
      "evidence_ids": []
    }
  ],
  "risk_interpretation": {
    "structural_assessment": "Structured reasoning about the building's structural vulnerability",
    "environmental_assessment": "Structured reasoning about environmental seismic hazards",
    "overall_reasoning": "Integrated reasoning explaining the overall risk assessment"
  },
  "confidence": 0.85
}

PRIORITY OF INFORMATION:
1. Assessment results produced by the ML model and hazard engine.
2. Retrieved engineering knowledge.
3. General reasoning.

If retrieved knowledge conflicts with assessment results, trust the assessment results.

STRICT RULES:
- Output ONLY valid JSON. Do not include markdown, code fences, or commentary.
- risk_interpretation is required
- "summary" MUST contain EXACTLY 6 items. No more and no fewer.
- "recommendations" MUST contain EXACTLY 5 items. No more and no fewer.
- Every recommendation MUST include a valid priority, title, description, and evidence_ids.
- evidence_ids MUST only reference chunk_ids shown in the RETRIEVED KNOWLEDGE section.
- If no retrieved knowledge supports an item, use an empty list [].
- Do not invent chunk_ids that were not provided in the references.
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

def create_llm_service(
    model: str = "gemini-2.5-flash",
    retriever: Optional[Any] = None,
) -> LLMService:
    client = GenAIClient(model=model)
    return LLMService(client=client, retriever=retriever)