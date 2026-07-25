"""
services/retrieval/query_builder.py

Builds deterministic retrieval queries from structured assessment data.

Each query targets a specific knowledge base category and is constructed
from the building and environmental context fields — no LLM calls involved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from project_schema import BuildingLLMContext, EnvironmentalContext


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────


@dataclass
class ChannelQuery:
    """
    A single retrieval query targeting one knowledge base category.

    Attributes:
        query: The text query string for semantic search.
        category_filter: ChromaDB ``$in`` filter on the ``category`` metadata field.
        tags_filter: Optional tags to boost in scoring (not a hard filter).
        k: Maximum number of results to return from this channel.
        channel_name: Human-readable label for logging and debugging.
    """

    query: str
    category_filter: List[str]
    tags_filter: Optional[List[str]] = None
    k: int = 2
    channel_name: str = ""


# ──────────────────────────────────────────────────────────────
# Query Builder
# ──────────────────────────────────────────────────────────────


class QueryBuilder:
    """
    Constructs per-channel retrieval queries from structured assessment data.

    Usage::

        builder = QueryBuilder()
        channels = builder.build(building_ctx, env_ctx)
    """

    # Material codes in BuildingLLMContext.substructure that map to KB tags
    MATERIAL_FIELDS = [
        "mud_mortar_stone",
        "cement_brick",
        "rc_engineered",
        "rc_non_engineered",
        "adobe_mud",
        "timber",
    ]

    def build(
        self,
        building: BuildingLLMContext,
        env: EnvironmentalContext,
    ) -> List[ChannelQuery]:
        """
        Build channel queries from assessment context.

        Returns three channels: building vulnerability, environmental, and local context.
        """
        return [
            self._build_vulnerability_channel(building),
            self._build_environmental_channel(env),
            self._build_local_context_channel(building, env),
        ]

    # ── Channel: Building Vulnerability ──────────────────────

    def _build_vulnerability_channel(
        self, building: BuildingLLMContext
    ) -> ChannelQuery:
        """Query for building vulnerability and mitigation knowledge."""
        parts: List[str] = []

        # Material description
        material_desc = self._material_description(building)
        if material_desc:
            parts.append(material_desc)

        # Structural characteristics
        structural = building.structural
        floors = structural.get("floors", 0)
        age = structural.get("age_years", 0)

        if floors and int(floors) > 3:
            parts.append(f"multi-story building with {floors} floors")
        if age and int(age) > 50:
            parts.append("older building age vulnerability")
        elif age and int(age) > 30:
            parts.append("moderate age structural fatigue")

        # Foundation and roof from material context
        material = building.material
        foundation = material.get("foundation_type", "")
        roof = material.get("roof_type", "")
        if foundation:
            parts.append(f"foundation type: {foundation}")
        if roof:
            parts.append(f"roof type: {roof}")

        # Active material tags for metadata boosting
        active_tags = self._active_material_tags(building)

        query = "; ".join(parts) if parts else "building structural vulnerability"
        return ChannelQuery(
            query=query,
            category_filter=["building_vulnerability", "mitigation"],
            tags_filter=active_tags,
            k=2,
            channel_name="building_vulnerability",
        )

    # ── Channel: Environmental ───────────────────────────────

    def _build_environmental_channel(
        self, env: EnvironmentalContext
    ) -> ChannelQuery:
        """Query for environmental hazard knowledge."""
        parts: List[str] = []

        # Hazard level
        hazard_level = getattr(env, "hazard_level", "")
        hazard_score = getattr(env, "hazard_score", 0.0)
        if hazard_level:
            parts.append(f"{hazard_level.lower()} seismic hazard")
        if hazard_score and float(hazard_score) > 70:
            parts.append("high hazard score area")

        # Soil information
        soil = getattr(env, "soil", None)
        if soil is not None:
            soil_class = getattr(soil, "classification", "")
            dominant_soil = getattr(soil, "dominant_soil", "")
            if soil_class:
                parts.append(f"soil class {soil_class}")
            if dominant_soil:
                parts.append(f"{dominant_soil} soil conditions")

        # Fault proximity
        faults = getattr(env, "faults", None)
        if faults is not None:
            fault_dist = getattr(faults, "distance_km", None)
            fault_class = getattr(faults, "classification", "")
            if fault_class:
                parts.append(f"fault proximity: {fault_class.lower()}")
            if fault_dist is not None and float(fault_dist) < 20:
                parts.append("close to active fault")

        # Historical activity
        hist = getattr(env, "historical_activity", None)
        if hist is not None:
            hist_class = getattr(hist, "classification", "")
            if hist_class:
                parts.append(f"historical seismicity: {hist_class.lower()}")

        query = "; ".join(parts) if parts else "environmental seismic hazard"
        return ChannelQuery(
            query=query,
            category_filter=["environmental_hazards"],
            k=2,
            channel_name="environmental",
        )

    # ── Channel: Local Context ───────────────────────────────

    def _build_local_context_channel(
        self, building: BuildingLLMContext, env: EnvironmentalContext
    ) -> ChannelQuery:
        """Query for Myanmar-specific local context knowledge."""
        parts: List[str] = ["Myanmar earthquake risk"]

        hazard_level = getattr(env, "hazard_level", "")
        if hazard_level:
            parts.append(hazard_level.lower())

        # Use the first summary sentence if available
        summary = getattr(env, "summary", [])
        if summary and len(summary) > 0:
            # Take a short prefix from the first summary point
            first = summary[0]
            if len(first) > 100:
                first = first[:100]
            parts.append(first)

        query = "; ".join(parts)
        return ChannelQuery(
            query=query,
            category_filter=["local_context"],
            k=1,
            channel_name="local_context",
        )

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _material_description(building: BuildingLLMContext) -> str:
        """Build a human-readable material description from substructure flags."""
        substructure = building.substructure
        active_materials = [
            name.replace("_", " ")
            for name in QueryBuilder.MATERIAL_FIELDS
            if substructure.get(name, False)
        ]
        if active_materials:
            return f"building with {' and '.join(active_materials)} superstructure"
        return ""

    @staticmethod
    def _active_material_tags(building: BuildingLLMContext) -> List[str]:
        """Return KB tags that match the building's active materials."""
        substructure = building.substructure
        tags: List[str] = []
        for field in QueryBuilder.MATERIAL_FIELDS:
            if substructure.get(field, False):
                tags.append(field)
        return tags