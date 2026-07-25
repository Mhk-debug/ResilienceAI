"""
services/retrieval/chunk_loader.py

Loads, validates, and chunks knowledge base Markdown documents.
Handles YAML frontmatter parsing, metadata validation, and semantic chunking.
"""

from __future__ import annotations

import os
import re
import logging
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

VALID_CATEGORIES = {
    "building_vulnerability",
    "earthquake_safety",
    "environmental_hazards",
    "local_context",
    "mitigation",
}

REQUIRED_FRONTMATTER_FIELDS = {"id", "category", "tags", "source"}

REQUIRED_SOURCE_FIELDS = {"title", "organization", "url"}

CHUNK_SEPARATORS = [
    r"^## Source",
    r"^## Retrofit Guidance",
    r"^## Retrofit Strategies?",
    r"^## Critical Improving Factors",
    r"^## Myanmar-Specific",
    r"^## Hazard Engine Integration",
    r"^## Cost-Benefit",
    r"^## Myanmar Adaptation",
    r"^## Building Implications",
]


@dataclass
class KnowledgeChunk:
    """A single retrievable chunk from the knowledge base."""

    chunk_id: str
    doc_id: str
    category: str
    tags: List[str]
    title: str
    text: str
    source_title: str
    source_org: str
    source_url: str
    source_license: Optional[str] = None
    chunk_index: int = 0
    total_chunks: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────
# Frontmatter Parser
# ──────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[Dict[str, Any], str, List[str]]:
    """
    Parse YAML frontmatter from a Markdown file.
    
    Returns:
        (metadata, body_content, warnings)
    """
    warnings: List[str] = []
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if not match:
        raise ValueError("No valid YAML frontmatter found (must begin and end with '---')")

    raw_yaml = match.group(1)
    body = match.group(2).strip()

    try:
        metadata = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")

    if not isinstance(metadata, dict):
        raise ValueError("Frontmatter must evaluate to a YAML mapping (dictionary).")

    if metadata is None:
        metadata = {}

    return metadata, body, warnings


def validate_frontmatter(
    metadata: Dict[str, Any], file_path: str
) -> List[str]:
    """
    Validate that frontmatter contains all required fields and values.
    
    Returns a list of error messages. An empty list means validation passed.
    """
    errors: List[str] = []
    basename = os.path.basename(file_path)

    # Check required top-level fields
    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in metadata or metadata[field] is None:
            errors.append(f"[{basename}] Missing required frontmatter field: '{field}'")

    # Validate 'id' is a non-empty string
    doc_id = metadata.get("id")
    if doc_id is not None and not isinstance(doc_id, str):
        errors.append(f"[{basename}] Field 'id' must be a string, got {type(doc_id).__name__}")

    # Validate 'category'
    category = metadata.get("category")
    if category is not None:
        if isinstance(category, str):
            if category not in VALID_CATEGORIES:
                errors.append(
                    f"[{basename}] Invalid category '{category}'. "
                    f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
                )
        else:
            errors.append(f"[{basename}] Field 'category' must be a string")

    # Validate 'tags' is a list
    tags = metadata.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append(f"[{basename}] Field 'tags' must be a list, got {type(tags).__name__}")

    # Validate 'source' block
    source = metadata.get("source")
    if source is not None:
        if isinstance(source, dict):
            for sf in REQUIRED_SOURCE_FIELDS:
                if sf not in source:
                    errors.append(f"[{basename}] Missing required source field: '{sf}'")
        else:
            errors.append(f"[{basename}] Field 'source' must be a mapping (dictionary)")

    # Validate 'applies_when' if present (must be a dict)
    applies = metadata.get("applies_when")
    if applies is not None and not isinstance(applies, dict):
        errors.append(
            f"[{basename}] Field 'applies_when' must be a mapping, "
            f"got {type(applies).__name__}"
        )

    return errors


# ──────────────────────────────────────────────────────────────
# Chunking
# ──────────────────────────────────────────────────────────────

def guess_title(body: str) -> str:
    """Extract the first H1 heading (# Title) from the body."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.lstrip("# ").strip()
    return "Untitled"


def chunk_document(body: str) -> List[str]:
    """
    Split a document body into semantic chunks based on section headings.
    
    For small documents (< 600 chars), returns a single chunk.
    For larger documents, splits at major section boundaries defined by
    CHUNK_SEPARATORS.
    """
    if len(body) < 600:
        return [body]

    chunks = []

    # Build a normalized pattern from separators
    sep_pattern = "|".join(f"(?:{pat})" for pat in CHUNK_SEPARATORS)
    split_points = list(re.finditer(sep_pattern, body, re.MULTILINE))

    if not split_points:
        return [body]

    # Split between separators
    prev_end = 0
    for match in split_points:
        start = match.start()
        if start > prev_end:
            section = body[prev_end:start].strip()
            if section:
                chunks.append(section)
        prev_end = start

    # Remaining text after last separator
    remaining = body[prev_end:].strip()
    if remaining:
        chunks.append(remaining)

    # If chunking produced only one chunk, return it
    if len(chunks) <= 1:
        return [body]

    return [c for c in chunks if c]


# ──────────────────────────────────────────────────────────────
# Document Loader
# ──────────────────────────────────────────────────────────────

class ChunkLoader:
    """
    Walks the knowledge base directory, parses frontmatter, validates,
    chunks documents, and returns KnowledgeChunk instances.
    """

    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = knowledge_dir
        if not os.path.isdir(knowledge_dir):
            raise ValueError(
                f"Knowledge directory does not exist: {knowledge_dir}"
            )

    def load_all(self) -> List[KnowledgeChunk]:
        """
        Load all knowledge documents, validate, chunk, and return chunks.
        
        Raises:
            ValueError: If any document fails validation.
        """
        md_files = self._find_md_files()
        if not md_files:
            logger.warning(
                "No Markdown files found in %s", self.knowledge_dir
            )
            return []

        all_chunks: List[KnowledgeChunk] = []
        seen_ids: set[str] = set()
        total_errors = 0

        for file_path in sorted(md_files):
            try:
                chunks = self._process_file(file_path, seen_ids)
                all_chunks.extend(chunks)
            except ValueError as e:
                total_errors += 1
                logger.error("Skipping %s: %s", file_path, e)

        if total_errors > 0:
            raise ValueError(
                f"{total_errors} document(s) failed validation. "
                "Fix errors above before proceeding."
            )

        logger.info(
            "Loaded %d chunks from %d documents",
            len(all_chunks),
            len(md_files),
        )
        return all_chunks

    def _find_md_files(self) -> List[str]:
        """Recursively find all .md files in the knowledge directory."""
        md_files: List[str] = []
        for root, _, files in os.walk(self.knowledge_dir):
            for fname in files:
                if fname.endswith(".md"):
                    md_files.append(os.path.join(root, fname))
        return md_files

    def _process_file(
        self, file_path: str, seen_ids: set[str]
    ) -> List[KnowledgeChunk]:
        """Process a single Markdown file into chunks."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        if not raw_text.strip():
            raise ValueError(f"Empty document: {file_path}")

        metadata, body, _warnings = parse_frontmatter(raw_text)

        # Validate
        errors = validate_frontmatter(metadata, file_path)
        if errors:
            error_msg = "; ".join(errors)
            raise ValueError(f"Validation failed: {error_msg}")

        doc_id: str = metadata["id"]

        # Check for duplicate IDs
        if doc_id in seen_ids:
            raise ValueError(f"Duplicate document ID: '{doc_id}'")
        seen_ids.add(doc_id)

        category: str = metadata["category"]
        tags: List[str] = metadata.get("tags", [])
        source: dict = metadata.get("source", {})
        source_title: str = source.get("title", "Unknown")
        source_org: str = source.get("organization", "Unknown")
        source_url: str = source.get("url", "")
        source_license: Optional[str] = source.get("license")

        # Build extra metadata
        extra_metadata: Dict[str, Any] = {}
        if "applies_when" in metadata:
            extra_metadata["applies_when"] = metadata["applies_when"]
        if "supplementary" in source:
            extra_metadata["supplementary_sources"] = source["supplementary"]

        title = guess_title(body)
        chunks = chunk_document(body)

        results: List[KnowledgeChunk] = []
        for i, section_text in enumerate(chunks):
            chunk_id = f"{doc_id}__chunk_{i}"
            results.append(
                KnowledgeChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    category=category,
                    tags=tags,
                    title=title,
                    text=section_text,
                    source_title=source_title,
                    source_org=source_org,
                    source_url=source_url,
                    source_license=source_license,
                    chunk_index=i,
                    total_chunks=len(chunks),
                    metadata=extra_metadata,
                )
            )

        logger.debug(
            "  -> %s: %d chunk(s) [%s]",
            os.path.basename(file_path),
            len(chunks),
            category,
        )
        return results