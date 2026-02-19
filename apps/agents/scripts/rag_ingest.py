#!/usr/bin/env python
"""
Unified CLI for initializing Pinecone index and ingesting sample data.

Usage:
    python -m scripts.rag_ingest init --config config.yaml
    python -m scripts.rag_ingest ingest --config config.yaml --dataset-path /path/to/data
    python -m scripts.rag_ingest full --config config.yaml --dataset-path /path/to/data
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from agents.providers.rag.settings import EnvSettings, load_config
from agents.providers.rag.utils.logging import setup_logging
from agents.providers.rag.ingest.build_index import main as build_index_main
from agents.providers.rag.ingest.ingest_csv import main as ingest_csv_main

logger = logging.getLogger(__name__)


def init_index(config: Optional[str] = None) -> None:
    """Initialize Pinecone indexes."""
    logger.info("Initializing Pinecone indexes...")

    # Save original sys.argv and replace with args for build_index
    orig_argv = sys.argv
    try:
        sys.argv = ["build_index.py"]
        if config:
            sys.argv.extend(["--config", config])
        build_index_main()
    finally:
        sys.argv = orig_argv

    logger.info("Index initialization complete!")


def ingest_data(
    config: Optional[str] = None,
    dataset_path: Optional[str] = None,
    csv_path: Optional[str] = None,
    limit: Optional[int] = None,
    namespace: str = "__default__",
) -> None:
    """Ingest data into Pinecone indexes."""
    logger.info("Ingesting data into Pinecone indexes...")

    # Save original sys.argv and replace with args for ingest_csv
    orig_argv = sys.argv
    try:
        sys.argv = ["ingest_csv.py"]
        if config:
            sys.argv.extend(["--config", config])
        if dataset_path:
            sys.argv.extend(["--zip-path", dataset_path])
        if csv_path:
            sys.argv.extend(["--csv-path", csv_path])
        if limit:
            sys.argv.extend(["--limit", str(limit)])
        sys.argv.extend(["--namespace", namespace])
        ingest_csv_main()
    finally:
        sys.argv = orig_argv

    logger.info("Data ingestion complete!")


def full_setup(
    config: Optional[str] = None,
    dataset_path: Optional[str] = None,
    csv_path: Optional[str] = None,
    limit: Optional[int] = None,
    namespace: str = "__default__",
) -> None:
    """Initialize index and ingest data in one step."""
    init_index(config=config)
    ingest_data(
        config=config,
        dataset_path=dataset_path,
        csv_path=csv_path,
        limit=limit,
        namespace=namespace,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified CLI for Pinecone index initialization and data ingestion"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Init subcommand
    init_parser = subparsers.add_parser("init", help="Initialize Pinecone indexes")
    init_parser.add_argument("--config", default=None, help="Path to config.yaml")

    # Ingest subcommand
    ingest_parser = subparsers.add_parser("ingest", help="Ingest data into Pinecone indexes")
    ingest_parser.add_argument("--config", default=None, help="Path to config.yaml")
    ingest_parser.add_argument(
        "--dataset-path",
        default=None,
        help="Path to zip file or directory containing CSV and images",
    )
    ingest_parser.add_argument(
        "--csv-path",
        default=None,
        help="Path to CSV within zip file or filesystem",
    )
    ingest_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of rows to ingest",
    )
    ingest_parser.add_argument(
        "--namespace",
        default="__default__",
        help="Pinecone namespace to use",
    )

    # Full setup subcommand
    full_parser = subparsers.add_parser(
        "full",
        help="Initialize indexes and ingest data (full setup)",
    )
    full_parser.add_argument("--config", default=None, help="Path to config.yaml")
    full_parser.add_argument(
        "--dataset-path",
        default=None,
        help="Path to zip file or directory containing CSV and images",
    )
    full_parser.add_argument(
        "--csv-path",
        default=None,
        help="Path to CSV within zip file or filesystem",
    )
    full_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of rows to ingest",
    )
    full_parser.add_argument(
        "--namespace",
        default="__default__",
        help="Pinecone namespace to use",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        init_index(config=args.config)
    elif args.command == "ingest":
        ingest_data(
            config=args.config,
            dataset_path=args.dataset_path,
            csv_path=args.csv_path,
            limit=args.limit,
            namespace=args.namespace,
        )
    elif args.command == "full":
        full_setup(
            config=args.config,
            dataset_path=args.dataset_path,
            csv_path=args.csv_path,
            limit=args.limit,
            namespace=args.namespace,
        )


if __name__ == "__main__":
    setup_logging()
    main()
