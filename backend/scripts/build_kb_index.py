"""
scripts/build_kb_index.py

Standalone script to build or rebuild the ChromaDB vector index from the
knowledge base.

Usage:
    python scripts/build_kb_index.py                   # Default build
    python scripts/build_kb_index.py --verbose          # Detailed logging
    python scripts/build_kb_index.py --force            # Force rebuild even if exists
    python scripts/build_kb_index.py --check            # Check if index exists (no-op)
"""

from __future__ import annotations

import argparse
import logging
import sys
import os

# Add the backend directory to the path so we can import services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.retrieval.indexer import get_indexer

logger = logging.getLogger("build_kb_index")


def setup_logging(verbose: bool = False):
    """Configure logging with appropriate verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main():
    parser = argparse.ArgumentParser(
        description="Build or rebuild the ChromaDB vector index from the knowledge base.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug-level logging.",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force rebuild even if index already exists.",
    )
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Check if index exists (exit 0 if exists, exit 1 if not).",
    )
    parser.add_argument(
        "--chroma-dir",
        type=str,
        default=None,
        help="Override the default ChromaDB directory.",
    )
    parser.add_argument(
        "--knowledge-dir",
        type=str,
        default=None,
        help="Override the default knowledge base directory.",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Create the indexer
    indexer = get_indexer(
        chroma_dir=args.chroma_dir,
        knowledge_dir=args.knowledge_dir,
    )

    # ── Check mode ───────────────────────────────────────────
    if args.check:
        exists = indexer.index_exists()
        if exists:
            logger.info("Index EXISTS at %s", indexer.chroma_dir)
            sys.exit(0)
        else:
            logger.info("Index NOT FOUND at %s", indexer.chroma_dir)
            sys.exit(1)

    # ── Rebuild protection ───────────────────────────────────
    if not args.force and indexer.index_exists():
        logger.warning(
            "Index already exists at %s. Use --force to rebuild.",
            indexer.chroma_dir,
        )
        logger.warning("Aborting to avoid accidental re-indexing.")
        sys.exit(0)

    # ── Build ────────────────────────────────────────────────
    try:
        count = indexer.build()
        if count > 0:
            logger.info(
                "Successfully indexed %d chunks. ChromaDB location: %s",
                count,
                indexer.chroma_dir,
            )
            sys.exit(0)
        else:
            logger.error("No chunks were indexed. Check the knowledge base.")
            sys.exit(1)
    except ValueError as e:
        logger.error("Build failed: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during index build: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()