from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from RAG.settings import EnvSettings, load_config
from RAG.utils.dynamic_import import import_from_path
from RAG.utils.hashing import sha256_hex
from RAG.pinecone_store import (
    build_pinecone_client,
    ensure_index,
    get_index,
    index_name,
)
from RAG.context.canonicalize import canonicalize_feature_state
from RAG.context.manus import ManusCanonicalizer
from RAG.embedder.openai_embed import OpenAITextEmbedder
from RAG.embedder.numeric import NumericFeatureEmbedder
from RAG.embedder.clip_image import ClipImageEmbedder
from RAG.utils.logging import setup_logging
from feature_extractor.graph import build_graph
from feature_extractor.llm_client import GeminiVisionClient
from feature_extractor.types import ArtworkMetadata, FeatureState

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--zip-path", default=None, help="Path to a zip that contains the CSV + images")
    parser.add_argument("--csv-path", default=None, help="CSV path (within zip or filesystem)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows ingested")
    parser.add_argument("--namespace", default="__default__", help="Pinecone namespace")
    args = parser.parse_args()

    cfg = load_config(args.config)
    env = EnvSettings()
    mode = cfg.embedding_mode

    zip_path = args.zip_path or cfg.get("dataset", "default_zip_path")
    csv_path = args.csv_path or cfg.get("dataset", "default_csv_path_in_zip")

    rows, zip_handle = load_rows(zip_path, csv_path, limit=args.limit)

    feature_import = cfg.get("feature_extractor", "import_path", default="") or ""
    feature_fn = None
    if feature_import.strip():
        feature_fn = import_from_path(feature_import.strip())

    pc = build_pinecone_client(env.PINECONE_API_KEY)

    prefix = cfg.get("pinecone", "index_prefix", default="artium")
    metric = cfg.get("pinecone", "metric", default="cosine")
    cloud = cfg.get("pinecone", "cloud", default="aws")
    region = cfg.get("pinecone", "region", default="us-east-1")

    # Prepare embedders per mode
    text_embedder = None
    manus = None
    numeric_embedder = None
    image_embedder = None
    feature_graph = None

    if mode == "feature_text":
        o = cfg.get("feature_text", "openai_embeddings", default={})
        text_embedder = OpenAITextEmbedder(
            api_key=env.OPENAI_API_KEY,
            base_url=env.OPENAI_BASE_URL,
            model=o.get("model", "text-embedding-3-small"),
            dimensions=o.get("dimensions", 768),
            encoding_format=o.get("encoding_format", "float"),
        )
        manus_enabled = bool(cfg.get("feature_text", "manus", "enabled", default=False))
        if manus_enabled:
            if not env.MANUS_API_KEY:
                raise ValueError("MANUS_API_KEY is required when feature_text.manus.enabled=true")
            m = cfg.get("feature_text", "manus", default={})
            manus = ManusCanonicalizer(
                api_key_header=env.MANUS_API_KEY,
                agent_profile=m.get("agent_profile", "manus-1.6"),
                task_mode=m.get("task_mode", "agent"),
            )
        # Build feature extraction graph for feature_text mode
        logger.info("Building feature extraction graph...")
        feature_graph = build_graph(vision_llm=GeminiVisionClient())
        logger.info("Feature extraction graph built successfully")
    elif mode == "numeric":
        if feature_fn is None:
            raise ValueError("feature_extractor.import_path is required for numeric mode")
        fmap = cfg.get("numeric", "feature_map", default={})
        numeric_embedder = NumericFeatureEmbedder(feature_map=fmap)
    elif mode == "image":
        clip_cfg = cfg.get("image", "clip", default={})
        image_embedder = ClipImageEmbedder(
            model_name=clip_cfg.get("model", "clip-ViT-B-32"),
            device=clip_cfg.get("device", "cpu"),
        )
    else:
        raise ValueError(f"Unknown embedding_mode={mode}")

    # Ensure indexes exist with the correct dimensions.
    dims = {}
    if mode == "feature_text":
        dims = {"painting": text_embedder.dimension, "sculpture": text_embedder.dimension}
    elif mode == "numeric":
        dims = {
            "painting": numeric_embedder.dimension_for_type("painting"),
            "sculpture": numeric_embedder.dimension_for_type("sculpture"),
        }
    elif mode == "image":
        dims = {"painting": image_embedder.dimension, "sculpture": image_embedder.dimension}

    for t in ("painting", "sculpture"):
        ensure_index(
            pc=pc,
            name=index_name(prefix, mode, t),
            dimension=dims[t],
            metric=metric,
            cloud=cloud,
            region=region,
        )

    # Prepare Index clients
    idx = {
        "painting": get_index(pc, index_name(prefix, mode, "painting")),
        "sculpture": get_index(pc, index_name(prefix, mode, "sculpture")),
    }

    # Ingest rows
    batch: List[Tuple[str, List[float], Dict[str, Any]]] = []
    upsert_batch_size = 100

    notes_cfg = cfg.get("feature_text", "notes", default={})
    strip_urls = bool(notes_cfg.get("strip_urls", True))
    max_total = int(notes_cfg.get("max_chars_total", 800))
    max_section = int(notes_cfg.get("max_chars_per_section", 250))

    for i, row in enumerate(rows):
        image_ref = row.get("image_file") or row.get("image_path") or row.get("image_ref")
        if not image_ref:
            logger.warning("Skipping row %s: missing image_file/image_ref", i)
            continue

        # Load image
        image_bytes = load_image_from_zip(zip_handle, image_ref, zip_path=zip_path)

        # Minimal metadata stored in Pinecone (exclude image-specific technical fields)
        exclude_fields = {
            "full_page_file",
            "image_bbox_pdf_units_xyxy",
            "image_block_number",
            "image_ext",
            "image_file",
            "image_height_px",
            "image_index_on_page",
            "image_ref",
            "image_width_px",
        }
        metadata: Dict[str, Any] = {k: _safe_meta(v) for k, v in row.items() if k not in exclude_fields}

        # === FEATURE EXTRACTION ===
        artwork_type = None
        vec = None
        
        if mode == "feature_text":
            # Feature extraction graph determines artwork_type
            metadata_obj = ArtworkMetadata(
                title=row.get("title", "Unknown"),
                author=row.get("author", "Unknown"),
                year=row.get("year"),
                medium_hint=row.get("medium_hint"),
            )
            initial_state: FeatureState = {
                "metadata": metadata_obj.model_dump(),
                "image_bytes": image_bytes,
                "image_mode": "RGB",
                "image_size": (1024, 1024),
                "errors": [],
            }
            logger.info(f"Running feature extraction graph for row {i}...")
            feature_state = feature_graph.invoke(initial_state)
            artwork_type = feature_state.get("artwork_type", "").lower().strip()
            
            # === CHECK ARTWORK TYPE ===
            if artwork_type not in ("painting", "sculpture"):
                logger.warning("Skipping row %s: unknown artwork_type=%r from classifier", i, artwork_type)
                continue
            
            # === BUILD VECTOR ===
            vision_features = feature_state.get("vision_features") or {}
            feature_state.pop("market_features", None)
            
            schema_version = (
                cfg.get("feature_text", "schema_version_painting")
                if artwork_type == "painting"
                else cfg.get("feature_text", "schema_version_sculpture")
            )
            if manus is None:
                canon_text, canon_json = canonicalize_feature_state(
                    feature_state,
                    strip_urls=strip_urls,
                    max_chars_total=max_total,
                    max_chars_per_section=max_section,
                    schema_version=schema_version,
                )
            else:
                type_instr = (
                    "For paintings: include medium/support if available; brushstroke/blending signals if present."
                    if artwork_type == "painting"
                    else "For sculptures: include material/form/surface/craftsmanship signals if present."
                )
                canon_json = manus.canonicalize(
                    feature_state, schema_version=schema_version, type_specific_instructions=type_instr
                )
                canon_text = _json_to_text(canon_json, max_chars=max_total)

            vec = text_embedder.embed_texts([canon_text])[0]
            metadata["canonical"] = json.dumps(canon_json)  # Convert dict to JSON string for Pinecone
            metadata["vector_mode"] = "feature_text"
            metadata["canonical_text_preview"] = canon_text[:200]
            
        elif mode == "numeric":
            # Feature function determines artwork_type
            feature_state = feature_fn(image_bytes=image_bytes, metadata=metadata)
            artwork_type = feature_state.get("artwork_type", "").lower().strip()
            
            # === CHECK ARTWORK TYPE ===
            if artwork_type not in ("painting", "sculpture"):
                logger.warning("Skipping row %s: unknown artwork_type=%r from feature function", i, artwork_type)
                continue
            
            # === BUILD VECTOR ===
            vision_features = feature_state.get("vision_features") or {}
            feature_state.pop("market_features", None)
            
            vec = numeric_embedder.build_vector(artwork_type, vision_features)
            metadata["vision_features"] = vision_features
            metadata["vector_mode"] = "numeric"
            
        elif mode == "image":
            # For image mode, we need to classify the image first to determine artwork_type
            logger.info(f"Classifying image for row {i} using feature graph...")
            metadata_obj = ArtworkMetadata(
                title=row.get("title", "Unknown"),
                author=row.get("author", "Unknown"),
                year=row.get("year"),
                medium_hint=row.get("medium_hint"),
            )
            initial_state: FeatureState = {
                "metadata": metadata_obj.model_dump(),
                "image_bytes": image_bytes,
                "image_mode": "RGB",
                "image_size": (1024, 1024),
                "errors": [],
            }
            # Build a minimal graph just to get classification
            from feature_extractor.classifier_node import artwork_classifier_node
            classifier = artwork_classifier_node(GeminiVisionClient())
            from langgraph.types import Command
            result = classifier(initial_state)
            if isinstance(result, Command):
                initial_state.update(result.update or {})
            artwork_type = initial_state.get("artwork_type", "").lower().strip()
            
            # === CHECK ARTWORK TYPE ===
            if artwork_type not in ("painting", "sculpture"):
                logger.warning("Skipping row %s: unknown artwork_type=%r from image classifier", i, artwork_type)
                continue
            
            # === BUILD VECTOR ===
            vec = image_embedder.embed_image(image_bytes)
            metadata["vector_mode"] = "image"

        # === INGEST TO CORRESPONDING INDEX ===
        lot_id = str(row.get("lot_number") or row.get("id") or f"row{i}")
        vec_id = f"{artwork_type}:{lot_id}:{sha256_hex(image_bytes)[:12]}"

        batch.append((vec_id, vec, metadata))

        if len(batch) >= upsert_batch_size:
            flush_batch(idx[artwork_type], batch, namespace=args.namespace)
            batch.clear()

    if batch:
        # Mixed types possible; flush per type
        by_type: Dict[str, List[Tuple[str, List[float], Dict[str, Any]]]] = {"painting": [], "sculpture": []}
        for vid, v, m in batch:
            t = vid.split(":", 1)[0]
            by_type[t].append((vid, v, m))
        for t, items in by_type.items():
            if items:
                flush_batch(idx[t], items, namespace=args.namespace)

    logger.info("Done ingestion.")


def _safe_meta(v: Any) -> Any:
    # Pinecone metadata supports: str, int, float, bool, list[str|int|float|bool], dict[str -> ...]
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    # pandas NaN
    try:
        import math

        if isinstance(v, float) and math.isnan(v):
            return None
    except Exception:
        pass
    return str(v)


def _json_to_text(obj: Dict[str, Any], max_chars: int = 800) -> str:
    # Stable order; avoid overly long string fields.
    lines: List[str] = []
    lines.append(f"type: {obj.get('type','')}")
    lines.append(f"schema_version: {obj.get('schema_version','')}")
    signals = obj.get("signals", {}) or {}
    for k in sorted(signals.keys()):
        lines.append(f"{k}: {signals.get(k)}")
    notes = obj.get("notes", {}) or {}
    for k in sorted(notes.keys()):
        val = notes.get(k, "")
        if isinstance(val, str) and val.strip():
            s = val.strip()
            if len(s) > 250:
                s = s[:249] + "…"
            lines.append(f"note_{k}: {s}")
    text = "\n".join(lines)
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "…"


def flush_batch(index, batch: List[Tuple[str, List[float], Dict[str, Any]]], namespace: str) -> None:
    vectors = [(vid, vec, meta) for (vid, vec, meta) in batch]
    index.upsert(vectors=vectors, namespace=namespace)
    logger.info("Upserted %d vectors into %s", len(vectors), namespace)


def load_rows(zip_path: str, csv_path: str, limit: Optional[int]) -> Tuple[List[Dict[str, Any]], Optional[zipfile.ZipFile]]:
    zp = Path(zip_path)
    if zp.exists() and zp.suffix.lower() == ".zip":
        z = zipfile.ZipFile(zp)
        with z.open(csv_path) as f:
            df = pd.read_csv(f)
        rows = df.to_dict(orient="records")
        if limit:
            rows = rows[:limit]
        return rows, z
    else:
        # filesystem csv
        p = Path(csv_path)
        df = pd.read_csv(p)
        rows = df.to_dict(orient="records")
        if limit:
            rows = rows[:limit]
        return rows, None


def load_image_from_zip(z: Optional[zipfile.ZipFile], image_ref: str, zip_path: str) -> bytes:
    if z is None:
        # Filesystem mode: resolve image_ref relative to dataset directory
        zip_dir = Path(zip_path)
        ref = str(image_ref).lstrip("./")
        candidates = [
            zip_dir / ref,  # as-is
            zip_dir / "pdf_extracted" / ref,  # under pdf_extracted/
            zip_dir / "pdf_extracted" / "images" / ref.split("/")[-1],  # just filename under pdf_extracted/images/
            zip_dir / "dataset" / ref,  # under dataset/
            zip_dir / "images" / ref.split("/")[-1],  # just filename under images/
        ]
        
        for c in candidates:
            if c.exists():
                return c.read_bytes()
        
        # If nothing found, list available images for debugging
        import glob
        available = list(glob.glob(str(zip_dir) + "/**/*.png", recursive=True))
        available += list(glob.glob(str(zip_dir) + "/**/*.jpg", recursive=True))
        logger.error(
            f"Could not find image '{image_ref}' in directory '{zip_path}'. Tried: {[str(c) for c in candidates]}. "
            f"Available images: {available[:10]}"
        )
        raise FileNotFoundError(f"Could not find image '{image_ref}' in directory '{zip_path}'")
    
    # Zip mode: try multiple candidates within the zip
    ref = str(image_ref).lstrip("./")
    candidates = [
        ref,  # as-is
        f"pdf_extracted/{ref}",  # under pdf_extracted/
        f"pdf_extracted/images/{ref.split('/')[-1]}",  # just filename under pdf_extracted/images/
        f"dataset/{ref}",  # under dataset/
        f"images/{ref.split('/')[-1]}",  # just filename under images/
        ref.split("/")[-1],  # just filename
    ]
    
    for c in candidates:
        try:
            return z.read(c)
        except KeyError:
            continue
    
    # If nothing found, list available paths for debugging
    available = z.namelist()
    image_files = [f for f in available if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    logger.error(
        f"Could not find image '{image_ref}' in zip '{zip_path}'. Tried: {candidates}. "
        f"Available images in zip: {image_files[:10]}"
    )
    raise FileNotFoundError(f"Could not find image '{image_ref}' in zip '{zip_path}'")


if __name__ == "__main__":
    setup_logging()
    main()
