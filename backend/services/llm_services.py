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
        result = self.client.generate(prompt, schema=schema)
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
   MAXIMUM WORD COUNT: 45
   MINIMUM WORD COUNT: 35
   
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