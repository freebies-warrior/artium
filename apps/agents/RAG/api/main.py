from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from apps.agents.RAG.settings import EnvSettings, load_config
from apps.agents.RAG.utils.logging import setup_logging
from apps.agents.RAG.utils.image_io import data_url_to_bytes
from apps.agents.RAG.utils.hashing import sha256_hex

from apps.agents.RAG.pinecone_store import build_pinecone_client, get_index, index_name
from apps.agents.RAG.context.canonicalize import canonicalize_feature_state
from apps.agents.RAG.context.manus import ManusCanonicalizer
from apps.agents.RAG.embedder.openai_embed import OpenAITextEmbedder
from apps.agents.RAG.embedder.numeric import NumericFeatureEmbedder
from apps.agents.RAG.embedder.clip_image import ClipImageEmbedder


logger = logging.getLogger(__name__)

setup_logging()

cfg = load_config()
env = EnvSettings()

pc = build_pinecone_client(env.PINECONE_API_KEY)

prefix = cfg.get("pinecone", "index_prefix", default="artium")
mode = cfg.embedding_mode

# Prepare embedders
text_embedder = None
manus = None
numeric_embedder = None
image_embedder = None

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
            raise RuntimeError("MANUS_API_KEY is required when feature_text.manus.enabled=true")
        m = cfg.get("feature_text", "manus", default={})
        manus = ManusCanonicalizer(
            api_key_header=env.MANUS_API_KEY,
            agent_profile=m.get("agent_profile", "manus-1.6"),
            task_mode=m.get("task_mode", "agent"),
        )
elif mode == "numeric":
    fmap = cfg.get("numeric", "feature_map", default={})
    numeric_embedder = NumericFeatureEmbedder(feature_map=fmap)
elif mode == "image":
    clip_cfg = cfg.get("image", "clip", default={})
    image_embedder = ClipImageEmbedder(
        model_name=clip_cfg.get("model", "clip-ViT-B-32"),
        device=clip_cfg.get("device", "cpu"),
    )
else:
    raise RuntimeError(f"Unknown embedding_mode={mode}")

# Prepare pinecone Index objects for each type
index_clients = {
    "painting": get_index(pc, index_name(prefix, mode, "painting")),
    "sculpture": get_index(pc, index_name(prefix, mode, "sculpture")),
}


class QueryRequest(BaseModel):
    artwork_type: str = Field(..., description="painting or sculpture")
    top_k: int = Field(10, ge=1, le=50)
    namespace: str = Field("__default__")
    include_metadata: bool = True

    # Provide either extracted feature_state OR an image (url/data_url) for on-the-fly extraction.
    feature_state: Optional[Dict[str, Any]] = None

    # If feature_state is not provided, one of:
    image_url: Optional[str] = None
    image_data_url: Optional[str] = None  # data:<mime>;base64,...


class QueryResponse(BaseModel):
    embedding_mode: str
    index: str
    results: Any


class UpsertRequest(BaseModel):
    artwork_type: str = Field(..., description="painting or sculpture")
    namespace: str = Field("__default__")
    # Optional stable ID. If omitted, server derives one from feature_state content.
    record_id: Optional[str] = None
    image_ref: Optional[str] = None  # pointer only, not used for embedding

    # Extracted features (FeatureState-like dict). This is the production ingestion input.
    feature_state: Dict[str, Any]


class UpsertResponse(BaseModel):
    embedding_mode: str
    index: str
    namespace: str
    record_id: str
    upserted: bool



app = FastAPI(title="Arium VectorDB Agent", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "embedding_mode": mode}
@app.post("/upsert", response_model=UpsertResponse)
def upsert(req: UpsertRequest) -> UpsertResponse:
    artwork_type = req.artwork_type.lower().strip()
    if artwork_type not in ("painting", "sculpture"):
        raise HTTPException(status_code=400, detail="artwork_type must be 'painting' or 'sculpture'")

    if mode == "image":
        raise HTTPException(
            status_code=400,
            detail="embedding_mode=image requires image bytes; /upsert currently supports feature_text/numeric only.",
        )

    feature_state = dict(req.feature_state)
    feature_state["artwork_type"] = artwork_type
    feature_state.pop("market_features", None)

    # Build vector the same way as /query for non-image modes
    if mode == "numeric":
        vision_features = feature_state.get("vision_features") or {}
        vec = numeric_embedder.build_vector(artwork_type, vision_features)
        schema_version = "numeric_v1"
        canon_text = None
    else:
        notes_cfg = cfg.get("feature_text", "notes", default={})
        strip_urls = bool(notes_cfg.get("strip_urls", True))
        max_total = int(notes_cfg.get("max_chars_total", 800))
        max_section = int(notes_cfg.get("max_chars_per_section", 250))
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

    # Derive record id if not supplied
    rid = (req.record_id or "").strip()
    if not rid:
        stable_payload = {
            "artwork_type": artwork_type,
            "schema_version": schema_version,
            "metadata": feature_state.get("metadata") or {},
            "vision_features": feature_state.get("vision_features") or {},
        }
        rid = sha256_hex(_stable_dumps(stable_payload).encode("utf-8"))[:32]

    # Build metadata (keep it lean)
    md = feature_state.get("metadata") or {}
    meta_out = {
        "artwork_type": artwork_type,
        "title": md.get("title"),
        "author": md.get("author"),
        "year": md.get("year"),
        "medium_hint": md.get("medium_hint"),
        "image_ref": req.image_ref or md.get("image_ref"),
        "schema_version": schema_version,
    }

    # Optional: include canonical text for explainability (kept short)
    if canon_text:
        meta_out["canon_text"] = canon_text[:800]

    index = index_clients[artwork_type]
    index.upsert(
        namespace=req.namespace,
        vectors=[{"id": rid, "values": vec, "metadata": meta_out}],
    )

    return UpsertResponse(
        embedding_mode=mode,
        index=index_name(prefix, mode, artwork_type),
        namespace=req.namespace,
        record_id=rid,
        upserted=True,
    )




@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    artwork_type = req.artwork_type.lower().strip()
    if artwork_type not in ("painting", "sculpture"):
        raise HTTPException(status_code=400, detail="artwork_type must be 'painting' or 'sculpture'")

    # Production path: caller may provide extracted feature_state directly (no image bytes).
    if req.feature_state is not None:
        if mode == "image":
            raise HTTPException(
                status_code=400,
                detail="embedding_mode=image requires an image (image_url or image_data_url); feature_state-only queries are not supported.",
            )
        feature_state = dict(req.feature_state)
        feature_state["artwork_type"] = artwork_type
        feature_state.pop("market_features", None)
    else:
        image_bytes = _load_image_bytes(req)

        if mode == "image":
            vec = image_embedder.embed_image(image_bytes)
        else:
            raise HTTPException(
                status_code=400,
                detail="For feature_text/numeric modes, provide feature_state directly (pre-extracted). Feature extraction is only performed during ingestion.",
            )

    # Vector building for non-image modes
    if mode != "image":
        if mode == "numeric":
            vision_features = feature_state.get("vision_features") or {}
            vec = numeric_embedder.build_vector(artwork_type, vision_features)
        else:
            notes_cfg = cfg.get("feature_text", "notes", default={})
            strip_urls = bool(notes_cfg.get("strip_urls", True))
            max_total = int(notes_cfg.get("max_chars_total", 800))
            max_section = int(notes_cfg.get("max_chars_per_section", 250))
            schema_version = (
                cfg.get("feature_text", "schema_version_painting")
                if artwork_type == "painting"
                else cfg.get("feature_text", "schema_version_sculpture")
            )
            if manus is None:
                canon_text, _canon_json = canonicalize_feature_state(
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


    index = index_clients[artwork_type]
    res = index.query(
        namespace=req.namespace,
        vector=vec,
        top_k=req.top_k,
        include_metadata=req.include_metadata,
    )
    return QueryResponse(
        embedding_mode=mode,
        index=index_name(prefix, mode, artwork_type),
        results=res,
    )


def _load_image_bytes(req: QueryRequest) -> bytes:
    if req.image_data_url:
        b, _mime = data_url_to_bytes(req.image_data_url)
        return b
    if req.image_url:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(req.image_url)
            r.raise_for_status()
            return r.content
    raise HTTPException(status_code=400, detail="Provide image_url or image_data_url")


def _stable_dumps(obj: Dict[str, Any]) -> str:
    """Serialize to a stable JSON string for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _json_to_text(obj: Dict[str, Any], max_chars: int = 800) -> str:
    lines = []
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
