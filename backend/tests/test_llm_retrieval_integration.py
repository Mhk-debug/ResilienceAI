"""
tests/test_llm_retrieval_integration.py

Tests for the integration between the LLM service and the retrieval system.

These tests use mock retrievers to verify:
- Backward compatibility when no retriever is configured.
- Retrieved knowledge appears in the prompt.
- Clean formatting (no scores exposed to LLM).
- Graceful fallback on retrieval failure.
- Response schema remains unchanged.
- Evidence citation validation and map building.
"""

from __future__ import annotations

import os
import sys
import pytest
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.llm_services import LLMService, create_llm_service
from project_schema import (
    BuildingLLMContext,
    EnvironmentalContext,
    LLMAnalysisInput,
    LLMAnalysisOutput,
    EvidenceCitation,
    LLMHistoricalActivity,
    LLMFaultContext,
    LLMSoilContext,
    LLMGroundMotionContext,
)


# ──────────────────────────────────────────────────────────────
# Mock Retriever
# ──────────────────────────────────────────────────────────────


@dataclass
class MockRetrievalResult:
    """Matches the interface of RetrievalResult for testing."""
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    channel: str = ""


class MockRetriever:
    """
    A mock retriever that returns controlled results for testing.
    """

    def __init__(self, results: Optional[List[MockRetrievalResult]] = None):
        self.results = results or []
        self.retrieve_call_count = 0
        self.should_fail = False

    def retrieve(self, building: Any, env: Any) -> List[MockRetrievalResult]:
        """Simulate retrieval with configurable behavior."""
        self.retrieve_call_count += 1
        if self.should_fail:
            raise RuntimeError("Simulated retrieval failure")
        return self.results


# ──────────────────────────────────────────────────────────────
# Mock GenAIClient
# ──────────────────────────────────────────────────────────────


class MockGenAIClient:
    """
    A mock GenAI client that captures the prompt and returns a valid response.
    """

    def __init__(self):
        self.last_prompt: str = ""
        self.generate_call_count = 0

    def generate(
        self,
        prompt: str,
        schema: Dict[str, Any],
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Capture the prompt and return a minimal valid response."""
        self.last_prompt = prompt
        self.generate_call_count += 1
        return {
            "summary": [
                {"text": "Finding 1", "evidence_ids": ["doc1__chunk_0"]},
                {"text": "Finding 2", "evidence_ids": []},
                {"text": "Finding 3", "evidence_ids": []},
                {"text": "Finding 4", "evidence_ids": []},
                {"text": "Finding 5", "evidence_ids": []},
                {"text": "Finding 6", "evidence_ids": []},
            ],
            "recommendations": [
                {"priority": "red", "title": "Fix structural issue", "description": "Immediate action required.", "evidence_ids": ["doc1__chunk_0"]},
                {"priority": "orange", "title": "Retrofit weak points", "description": "High priority retrofit.", "evidence_ids": []},
                {"priority": "yellow", "title": "Improve bracing", "description": "Moderate improvement.", "evidence_ids": []},
                {"priority": "yellow", "title": "Add dampers", "description": "Consider energy dissipation.", "evidence_ids": []},
                {"priority": "green", "title": "Routine inspection", "description": "Schedule regular checks.", "evidence_ids": []},
            ],
            "risk_interpretation": {
                "structural_assessment": "Building has structural vulnerabilities.",
                "environmental_assessment": "High seismic hazard area.",
                "overall_reasoning": "Combined risk is significant.",
            },
            "confidence": 0.85,
        }


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────


@pytest.fixture
def mock_building_context() -> BuildingLLMContext:
    return BuildingLLMContext(
        structural={"floors": 3, "age_years": 60, "floor_area_sq_feets": 800, "height_feets": 24},
        material={"roof_type": "Bamboo", "foundation_type": "Mud mortar", "ground_floor_type": "Mud"},
        substructure={"mud_mortar_stone": True, "cement_brick": False, "rc_engineered": False,
                       "rc_non_engineered": False, "adobe_mud": False, "timber": False},
    )


@pytest.fixture
def mock_env_context() -> EnvironmentalContext:
    return EnvironmentalContext(
        hazard_score=85.0,
        hazard_level="Very High",
        historical_activity=LLMHistoricalActivity(
            classification="Very High", events_within_radius=25, largest_magnitude=7.7,
        ),
        faults=LLMFaultContext(distance_km=5.0, classification="Very High"),
        soil=LLMSoilContext(classification="E", dominant_soil="Soft clay"),
        ground_motion=LLMGroundMotionContext(estimated_mmi=9.0, estimated_pga_g=0.6, confidence=0.8),
        summary=["Very High seismic hazard zone.", "Building is 5 km from active fault."],
    )


@pytest.fixture
def mock_input(mock_building_context, mock_env_context) -> LLMAnalysisInput:
    return LLMAnalysisInput(
        building_context=mock_building_context,
        environmental_context=mock_env_context,
    )


@pytest.fixture
def mock_genai_client() -> MockGenAIClient:
    return MockGenAIClient()


@pytest.fixture
def sample_retrieval_results() -> List[MockRetrievalResult]:
    return [
        MockRetrievalResult(
            chunk_id="doc1__chunk_0",
            text="Mud mortar stone buildings are highly vulnerable to seismic shaking. "
                 "Typical failure modes include out-of-plane wall collapse and corner separation.",
            score=0.912,
            metadata={
                "category": "building_vulnerability",
                "title": "Mud Mortar Stone Vulnerability",
                "source_org": "FEMA",
                "source_url": "https://example.com/fema",
                "tags": "mud_mortar_stone,high_vulnerability",
            },
            channel="building_vulnerability",
        ),
        MockRetrievalResult(
            chunk_id="doc2__chunk_0",
            text="Soft clay soils (Site Class E) amplify seismic waves by 2-3x. "
                 "Liquefaction risk is high in saturated loose sands and silts.",
            score=0.734,
            metadata={
                "category": "environmental_hazards",
                "title": "Soil Amplification",
                "source_org": "USGS",
                "source_url": "https://example.com/usgs",
                "tags": "soil_amplification,liquefaction",
            },
            channel="environmental",
        ),
    ]


# ──────────────────────────────────────────────────────────────
# Tests: Backward Compatibility
# ──────────────────────────────────────────────────────────────


class TestBackwardCompatibility:
    """LLMService must work without a retriever (original behavior)."""

    def test_no_retriever_initialization(self, mock_genai_client):
        """Service should initialize without a retriever."""
        service = LLMService(client=mock_genai_client)
        assert service.retriever is None

    def test_analyze_without_retriever(self, mock_genai_client, mock_input):
        """analyze() should work when retriever is None."""
        service = LLMService(client=mock_genai_client)
        result, evidence_map = service.analyze(mock_input)
        assert isinstance(result, LLMAnalysisOutput)
        assert len(result.summary) == 6
        assert len(result.recommendations) == 5
        assert evidence_map == {}

    def test_create_llm_service_without_retriever(self):
        """Factory function should work without retriever."""
        service = create_llm_service()
        assert service.retriever is None

    def test_prompt_without_retriever_has_no_knowledge_section(self, mock_genai_client, mock_input):
        """Prompt should not contain RETRIEVED KNOWLEDGE when no retriever."""
        service = LLMService(client=mock_genai_client)
        service.analyze(mock_input)
        # The fixed prompt instructions mention "RETRIEVED KNOWLEDGE" (in the
        # output requirements), so assert on the section header (with colon)
        # that only appears when knowledge is actually injected.
        assert "RETRIEVED KNOWLEDGE:" not in mock_genai_client.last_prompt


# ──────────────────────────────────────────────────────────────
# Tests: Retrieval Integration
# ──────────────────────────────────────────────────────────────


class TestRetrievalIntegration:
    """LLMService must integrate retrieved knowledge into the prompt."""

    def test_retriever_injected_via_constructor(self, mock_genai_client, sample_retrieval_results):
        """Retriever should be injectable via constructor."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        assert service.retriever is retriever

    def test_retriever_called_during_analyze(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Retriever.retrieve() should be called during analyze()."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        assert retriever.retrieve_call_count == 1

    def test_retriever_called_only_once(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Retriever should be called exactly once per analyze()."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        assert retriever.retrieve_call_count == 1

    def test_prompt_contains_retrieved_knowledge(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Prompt should contain RETRIEVED KNOWLEDGE section when results exist."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        assert "RETRIEVED KNOWLEDGE" in mock_genai_client.last_prompt

    def test_prompt_contains_reference_text(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Prompt should contain the actual retrieved text."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        assert "Mud mortar stone buildings" in mock_genai_client.last_prompt
        assert "Soft clay soils" in mock_genai_client.last_prompt

    def test_prompt_contains_source_metadata(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Prompt should contain source/category metadata but NOT scores."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        prompt = mock_genai_client.last_prompt
        # Should contain metadata
        assert "FEMA" in prompt
        assert "USGS" in prompt
        assert "building_vulnerability" in prompt
        # Should NOT contain scores (sample scores use unique values so they
        # cannot collide with the fixed "confidence": 0.85 example in the
        # prompt's output-format instructions)
        assert "0.912" not in prompt
        assert "0.734" not in prompt

    def test_prompt_contains_reference_numbers(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Prompt should number references (Reference 1, Reference 2)."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        prompt = mock_genai_client.last_prompt
        assert "Reference 1" in prompt
        assert "Reference 2" in prompt

    def test_prompt_contains_chunk_id(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Prompt should contain chunk_id in each reference."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        prompt = mock_genai_client.last_prompt
        assert "[chunk_id: doc1__chunk_0]" in prompt
        assert "[chunk_id: doc2__chunk_0]" in prompt

    def test_prompt_knowledge_between_env_and_output(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Retrieved knowledge should appear between env context and output requirements."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        prompt = mock_genai_client.last_prompt
        env_idx = prompt.index("ENVIRONMENTAL CONTEXT")
        knowledge_idx = prompt.index("RETRIEVED KNOWLEDGE")
        output_idx = prompt.index("OUTPUT REQUIREMENTS")
        assert env_idx < knowledge_idx < output_idx


# ──────────────────────────────────────────────────────────────
# Tests: Empty Results
# ──────────────────────────────────────────────────────────────


class TestEmptyResults:
    """LLMService must handle empty retrieval results gracefully."""

    def test_empty_results_no_knowledge_section(self, mock_genai_client, mock_input):
        """Prompt should not contain RETRIEVED KNOWLEDGE when results are empty."""
        retriever = MockRetriever(results=[])
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        assert "RETRIEVED KNOWLEDGE:" not in mock_genai_client.last_prompt

    def test_empty_results_still_returns_valid_output(self, mock_genai_client, mock_input):
        """analyze() should still return valid output with empty results."""
        retriever = MockRetriever(results=[])
        service = LLMService(client=mock_genai_client, retriever=retriever)
        result, evidence_map = service.analyze(mock_input)
        assert isinstance(result, LLMAnalysisOutput)
        assert len(result.summary) == 6
        assert evidence_map == {}

    def test_empty_results_prompt_unchanged(self, mock_genai_client, mock_input):
        """Prompt without results should be identical to no-retriever prompt."""
        # First, get the baseline prompt (no retriever)
        baseline_service = LLMService(client=mock_genai_client)
        baseline_service.analyze(mock_input)
        baseline_prompt = mock_genai_client.last_prompt

        # Then, get prompt with empty retriever
        retriever = MockRetriever(results=[])
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        retrieval_prompt = mock_genai_client.last_prompt

        assert baseline_prompt == retrieval_prompt


# ──────────────────────────────────────────────────────────────
# Tests: Failure Handling
# ──────────────────────────────────────────────────────────────


class TestFailureHandling:
    """LLMService must handle retrieval failures gracefully."""

    def test_retrieval_failure_falls_back(self, mock_genai_client, mock_input):
        """analyze() should work when retrieval raises an exception."""
        retriever = MockRetriever(results=[])
        retriever.should_fail = True
        service = LLMService(client=mock_genai_client, retriever=retriever)
        result, evidence_map = service.analyze(mock_input)
        assert isinstance(result, LLMAnalysisOutput)
        assert len(result.summary) == 6
        assert evidence_map == {}

    def test_retrieval_failure_no_knowledge_section(self, mock_genai_client, mock_input):
        """Prompt should not contain RETRIEVED KNOWLEDGE when retrieval fails."""
        retriever = MockRetriever(results=[])
        retriever.should_fail = True
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        assert "RETRIEVED KNOWLEDGE:" not in mock_genai_client.last_prompt

    def test_retrieval_failure_prompt_unchanged(self, mock_genai_client, mock_input):
        """Prompt after failure should match no-retriever baseline."""
        baseline_service = LLMService(client=mock_genai_client)
        baseline_service.analyze(mock_input)
        baseline_prompt = mock_genai_client.last_prompt

        retriever = MockRetriever(results=[])
        retriever.should_fail = True
        service = LLMService(client=mock_genai_client, retriever=retriever)
        service.analyze(mock_input)
        failure_prompt = mock_genai_client.last_prompt

        assert baseline_prompt == failure_prompt


# ──────────────────────────────────────────────────────────────
# Tests: Response Schema
# ──────────────────────────────────────────────────────────────


class TestResponseSchema:
    """Response schema must remain unchanged regardless of retrieval."""

    def test_schema_with_retrieval(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Response schema should be valid with retrieval."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        result, evidence_map = service.analyze(mock_input)
        assert isinstance(result, LLMAnalysisOutput)
        # Verify all required fields
        assert hasattr(result, "summary")
        assert hasattr(result, "recommendations")
        assert hasattr(result, "risk_interpretation")
        assert hasattr(result, "confidence")

    def test_schema_without_retrieval(self, mock_genai_client, mock_input):
        """Response schema should be valid without retrieval."""
        service = LLMService(client=mock_genai_client)
        result, evidence_map = service.analyze(mock_input)
        assert isinstance(result, LLMAnalysisOutput)
        assert hasattr(result, "summary")
        assert hasattr(result, "recommendations")
        assert hasattr(result, "risk_interpretation")
        assert hasattr(result, "confidence")

    def test_schema_identical_with_and_without_retrieval(self, mock_genai_client, mock_input, sample_retrieval_results):
        """Both paths should produce the same schema type."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service_with = LLMService(client=mock_genai_client, retriever=retriever)
        service_without = LLMService(client=mock_genai_client)

        result_with, _ = service_with.analyze(mock_input)
        result_without, _ = service_without.analyze(mock_input)

        assert type(result_with) is type(result_without)
        assert result_with.model_dump().keys() == result_without.model_dump().keys()


# ──────────────────────────────────────────────────────────────
# Tests: Formatting
# ──────────────────────────────────────────────────────────────


class TestFormatting:
    """_format_retrieved_knowledge must produce clean output."""

    def test_format_no_scores(self, sample_retrieval_results):
        """Formatted output must not contain similarity scores."""
        formatted = LLMService._format_retrieved_knowledge(sample_retrieval_results)
        assert "0.912" not in formatted
        assert "0.734" not in formatted
        assert "score" not in formatted.lower()

    def test_format_contains_metadata(self, sample_retrieval_results):
        """Formatted output must contain source/category metadata."""
        formatted = LLMService._format_retrieved_knowledge(sample_retrieval_results)
        assert "FEMA" in formatted
        assert "USGS" in formatted
        assert "building_vulnerability" in formatted

    def test_format_contains_reference_numbers(self, sample_retrieval_results):
        """Formatted output must number references."""
        formatted = LLMService._format_retrieved_knowledge(sample_retrieval_results)
        assert "Reference 1" in formatted
        assert "Reference 2" in formatted

    def test_format_contains_chunk_id(self, sample_retrieval_results):
        """Formatted output must contain chunk_id in each reference."""
        formatted = LLMService._format_retrieved_knowledge(sample_retrieval_results)
        assert "[chunk_id: doc1__chunk_0]" in formatted
        assert "[chunk_id: doc2__chunk_0]" in formatted

    def test_format_empty_list(self):
        """Empty list should return empty string."""
        formatted = LLMService._format_retrieved_knowledge([])
        assert formatted == ""

    def test_format_single_result(self):
        """Single result should produce one reference."""
        results = [
            MockRetrievalResult(
                chunk_id="test__chunk_0",
                text="Test content.",
                score=0.9,
                metadata={"category": "test", "source_org": "TestOrg"},
                channel="test",
            )
        ]
        formatted = LLMService._format_retrieved_knowledge(results)
        assert "Reference 1" in formatted
        assert "TestOrg" in formatted
        assert "Test content." in formatted
        assert "Reference 2" not in formatted

    def test_format_handles_missing_metadata(self):
        """Format should handle results with minimal metadata."""
        results = [
            MockRetrievalResult(
                chunk_id="minimal__chunk_0",
                text="Minimal content.",
                score=0.5,
                metadata={},
                channel="",
            )
        ]
        formatted = LLMService._format_retrieved_knowledge(results)
        assert "Reference 1" in formatted
        assert "Minimal content." in formatted
        # Should fall back to "General" for missing category
        assert "General" in formatted


# ──────────────────────────────────────────────────────────────
# Tests: Evidence Citation
# ──────────────────────────────────────────────────────────────


class TestEvidenceValidation:
    """_validate_evidence_ids must correctly filter evidence IDs."""

    def test_valid_ids_kept(self):
        """Valid evidence IDs should be kept."""
        valid = {"doc1__chunk_0", "doc2__chunk_0"}
        result = LLMService._validate_evidence_ids(
            ["doc1__chunk_0", "doc2__chunk_0"], valid
        )
        assert result == ["doc1__chunk_0", "doc2__chunk_0"]

    def test_invalid_ids_filtered(self):
        """Invalid evidence IDs should be filtered out."""
        valid = {"doc1__chunk_0"}
        result = LLMService._validate_evidence_ids(
            ["doc1__chunk_0", "fake_id", "another_fake"], valid
        )
        assert result == ["doc1__chunk_0"]

    def test_all_invalid_returns_empty(self):
        """All invalid IDs should return empty list."""
        valid = {"doc1__chunk_0"}
        result = LLMService._validate_evidence_ids(
            ["fake_id", "another_fake"], valid
        )
        assert result == []

    def test_empty_ids_returns_empty(self):
        """Empty input should return empty list."""
        result = LLMService._validate_evidence_ids([], {"doc1__chunk_0"})
        assert result == []

    def test_empty_valid_set_returns_empty(self):
        """Empty valid set should return empty list."""
        result = LLMService._validate_evidence_ids(
            ["doc1__chunk_0"], set()
        )
        assert result == []


class TestEvidenceMapBuilding:
    """_build_evidence_map must correctly construct evidence citations."""

    def test_build_map_with_valid_citations(self, sample_retrieval_results):
        """Evidence map should include only cited+validated chunks."""
        llm_result = {
            "summary": [
                {"text": "Finding 1", "evidence_ids": ["doc1__chunk_0"]},
                {"text": "Finding 2", "evidence_ids": []},
            ],
            "recommendations": [
                {"priority": "red", "title": "Fix", "description": "Fix it.", "evidence_ids": ["doc1__chunk_0"]},
            ],
        }
        evidence_map = LLMService._build_evidence_map(
            sample_retrieval_results, llm_result
        )
        assert "doc1__chunk_0" in evidence_map
        assert "doc2__chunk_0" not in evidence_map  # Not cited
        assert isinstance(evidence_map["doc1__chunk_0"], EvidenceCitation)
        assert evidence_map["doc1__chunk_0"].source_org == "FEMA"
        assert evidence_map["doc1__chunk_0"].relevance_score == 0.912

    def test_build_map_with_invalid_ids(self, sample_retrieval_results):
        """Invalid cited IDs should be filtered out."""
        llm_result = {
            "summary": [
                {"text": "Finding 1", "evidence_ids": ["fake_id"]},
            ],
            "recommendations": [],
        }
        evidence_map = LLMService._build_evidence_map(
            sample_retrieval_results, llm_result
        )
        assert evidence_map == {}

    def test_build_map_no_citations(self, sample_retrieval_results):
        """No cited IDs should return empty map."""
        llm_result = {
            "summary": [
                {"text": "Finding 1", "evidence_ids": []},
            ],
            "recommendations": [
                {"priority": "red", "title": "Fix", "description": "Fix it.", "evidence_ids": []},
            ],
        }
        evidence_map = LLMService._build_evidence_map(
            sample_retrieval_results, llm_result
        )
        assert evidence_map == {}

    def test_build_map_empty_retrieval(self):
        """No retrieved results should return empty map."""
        llm_result = {
            "summary": [{"text": "Finding 1", "evidence_ids": ["doc1__chunk_0"]}],
            "recommendations": [],
        }
        evidence_map = LLMService._build_evidence_map([], llm_result)
        assert evidence_map == {}

    def test_build_map_excerpt_truncation(self, sample_retrieval_results):
        """Excerpt should be truncated to ~300 chars."""
        # Create a result with very long text
        long_text = "A" * 500
        results = [
            MockRetrievalResult(
                chunk_id="long__chunk_0",
                text=long_text,
                score=0.9,
                metadata={"category": "test", "source_org": "TestOrg"},
                channel="test",
            )
        ]
        llm_result = {
            "summary": [{"text": "Finding", "evidence_ids": ["long__chunk_0"]}],
            "recommendations": [],
        }
        evidence_map = LLMService._build_evidence_map(results, llm_result)
        assert "long__chunk_0" in evidence_map
        # Should be truncated (300 chars + "...")
        assert len(evidence_map["long__chunk_0"].excerpt) <= 304  # 300 + "..."

    def test_evidence_in_analyze_output(self, mock_genai_client, mock_input, sample_retrieval_results):
        """analyze() should return evidence_map alongside LLMAnalysisOutput."""
        retriever = MockRetriever(results=sample_retrieval_results)
        service = LLMService(client=mock_genai_client, retriever=retriever)
        result, evidence_map = service.analyze(mock_input)
        assert isinstance(result, LLMAnalysisOutput)
        assert isinstance(evidence_map, dict)
        # The mock returns evidence_ids for doc1__chunk_0, so it should be in the map
        assert "doc1__chunk_0" in evidence_map


# Run with: pytest tests/test_llm_retrieval_integration.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])