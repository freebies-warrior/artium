from __future__ import annotations

import ipaddress
import json
import logging
import socket
from contextlib import asynccontextmanager
from io import BytesIO
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlsplit

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from PIL import Image
from pydantic import BaseModel, Field

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.providers.rag.settings import EnvSettings, load_config
from agents.providers.rag.utils.hashing import sha256_hex
from agents.providers.rag.utils.image_io import data_url_to_bytes
from agents.providers.rag.utils.logging import setup_logging

from agents.providers.rag.context.canonicalize import canonicalize_feature_state
from agents.providers.rag.context.manus import ManusCanonicalizer
from agents.providers.rag.embedder.clip_image import ClipImageEmbedder
from agents.providers.rag.embedder.numeric import NumericFeatureEmbedder
from agents.providers.rag.embedder.openai_embed import OpenAITextEmbedder
from agents.providers.rag.pinecone_store import build_pinecone_client, get_index, index_name

logger = logging.getLogger(__name__)
MAX_REMOTE_IMAGE_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class _RagRuntime:
    cfg: Any
    env: Any
    prefix: str
    mode: str
    text_embedder: OpenAITextEmbedder | None
    manus: ManusCanonicalizer | None
    numeric_embedder: NumericFeatureEmbedder | None
    image_embedder: ClipImageEmbedder | None
    index_clients: dict[str, Any]


_runtime: _RagRuntime | None = None


def require_internal_token(
    internal_token: str = Header(..., alias="X-Internal-Token"),
) -> None:
    settings = EnvSettings()
    expected = settings.INTERNAL_TOKEN.strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_TOKEN is not configured",
        )
    if internal_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )


def _initialize_runtime() -> _RagRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime

    setup_logging()

    cfg = load_config()
    env = EnvSettings()

    pc = build_pinecone_client(env.require_pinecone_api_key())
    prefix = cfg.get("pinecone", "index_prefix", default="artium")
    mode = cfg.embedding_mode

    text_embedder = None
    manus = None
    numeric_embedder = None
    image_embedder = None

    if mode == "feature_text":
        o = cfg.get("feature_text", "openai_embeddings", default={})
        text_embedder = OpenAITextEmbedder(
            api_key=env.require_openai_api_key(),
            base_url=env.OPENAI_BASE_URL,
            model=o.get("model", "text-embedding-3-small"),
            dimensions=o.get("dimensions", 768),
            encoding_format=o.get("encoding_format", "float"),
        )
        manus_enabled = bool(cfg.get("feature_text", "manus", "enabled", default=False))
        if manus_enabled:
            m = cfg.get("feature_text", "manus", default={})
            manus = ManusCanonicalizer(
                api_key_header=env.require_manus_api_key(),
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

    index_clients = {
        "painting": get_index(pc, index_name(prefix, mode, "painting")),
        "sculpture": get_index(pc, index_name(prefix, mode, "sculpture")),
    }

    _runtime = _RagRuntime(
        cfg=cfg,
        env=env,
        prefix=prefix,
        mode=mode,
        text_embedder=text_embedder,
        manus=manus,
        numeric_embedder=numeric_embedder,
        image_embedder=image_embedder,
        index_clients=index_clients,
    )
    return _runtime


def _get_runtime() -> _RagRuntime:
    if _runtime is None:
        return _initialize_runtime()
    return _runtime


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _initialize_runtime()
    yield


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


app = FastAPI(
    title="Arium VectorDB Agent",
    version="0.1.0",
    lifespan=lifespan,
    dependencies=[Depends(require_internal_token)],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    runtime = _get_runtime()
    return {"ok": True, "embedding_mode": runtime.mode}


@app.post("/upsert", response_model=UpsertResponse)
def upsert(req: UpsertRequest) -> UpsertResponse:
    runtime = _get_runtime()

    artwork_type = req.artwork_type.lower().strip()
    if artwork_type not in ("painting", "sculpture"):
        raise HTTPException(
            status_code=400, detail="artwork_type must be 'painting' or 'sculpture'"
        )

    if runtime.mode == "image":
        raise HTTPException(
            status_code=400,
            detail="embedding_mode=image requires image bytes; /upsert currently supports feature_text/numeric only.",
        )

    feature_state = dict(req.feature_state)
    feature_state["artwork_type"] = artwork_type
    feature_state.pop("market_features", None)

    # Build vector the same way as /query for non-image modes
    if runtime.mode == "numeric":
        if runtime.numeric_embedder is None:
            raise RuntimeError("Numeric embedder is not initialized")
        vision_features = feature_state.get("vision_features") or {}
        vec = runtime.numeric_embedder.build_vector(artwork_type, vision_features)
        schema_version = "numeric_v1"
        canon_text = None
    else:
        if runtime.text_embedder is None:
            raise RuntimeError("Text embedder is not initialized")

        notes_cfg = runtime.cfg.get("feature_text", "notes", default={})
        strip_urls = bool(notes_cfg.get("strip_urls", True))
        max_total = int(notes_cfg.get("max_chars_total", 800))
        max_section = int(notes_cfg.get("max_chars_per_section", 250))
        schema_version = (
            runtime.cfg.get("feature_text", "schema_version_painting")
            if artwork_type == "painting"
            else runtime.cfg.get("feature_text", "schema_version_sculpture")
        )
        if runtime.manus is None:
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
            canon_json = runtime.manus.canonicalize(
                feature_state,
                schema_version=schema_version,
                type_specific_instructions=type_instr,
            )
            canon_text = _json_to_text(canon_json, max_chars=max_total)

        vec = runtime.text_embedder.embed_texts([canon_text])[0]

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

    index = runtime.index_clients[artwork_type]
    index.upsert(
        namespace=req.namespace,
        vectors=[{"id": rid, "values": vec, "metadata": meta_out}],
    )

    return UpsertResponse(
        embedding_mode=runtime.mode,
        index=index_name(runtime.prefix, runtime.mode, artwork_type),
        namespace=req.namespace,
        record_id=rid,
        upserted=True,
    )


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    runtime = _get_runtime()

    artwork_type = req.artwork_type.lower().strip()
    if artwork_type not in ("painting", "sculpture"):
        raise HTTPException(
            status_code=400, detail="artwork_type must be 'painting' or 'sculpture'"
        )

    # Production path: caller may provide extracted feature_state directly (no image bytes).
    if req.feature_state is not None:
        if runtime.mode == "image":
            raise HTTPException(
                status_code=400,
                detail="embedding_mode=image requires an image (image_url or image_data_url); feature_state-only queries are not supported.",
            )
        feature_state = dict(req.feature_state)
        feature_state["artwork_type"] = artwork_type
        feature_state.pop("market_features", None)
    else:
        image_bytes = _load_image_bytes(req)

        if runtime.mode == "image":
            if runtime.image_embedder is None:
                raise RuntimeError("Image embedder is not initialized")
            vec = runtime.image_embedder.embed_image(image_bytes)
        else:
            raise HTTPException(
                status_code=400,
                detail="For feature_text/numeric modes, provide feature_state directly (pre-extracted). Feature extraction is only performed during ingestion.",
            )

    # Vector building for non-image modes
    if runtime.mode != "image":
        if runtime.mode == "numeric":
            if runtime.numeric_embedder is None:
                raise RuntimeError("Numeric embedder is not initialized")
            vision_features = feature_state.get("vision_features") or {}
            vec = runtime.numeric_embedder.build_vector(artwork_type, vision_features)
        else:
            if runtime.text_embedder is None:
                raise RuntimeError("Text embedder is not initialized")
            notes_cfg = runtime.cfg.get("feature_text", "notes", default={})
            strip_urls = bool(notes_cfg.get("strip_urls", True))
            max_total = int(notes_cfg.get("max_chars_total", 800))
            max_section = int(notes_cfg.get("max_chars_per_section", 250))
            schema_version = (
                runtime.cfg.get("feature_text", "schema_version_painting")
                if artwork_type == "painting"
                else runtime.cfg.get("feature_text", "schema_version_sculpture")
            )
            if runtime.manus is None:
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
                canon_json = runtime.manus.canonicalize(
                    feature_state,
                    schema_version=schema_version,
                    type_specific_instructions=type_instr,
                )
                canon_text = _json_to_text(canon_json, max_chars=max_total)
            vec = runtime.text_embedder.embed_texts([canon_text])[0]

    index = runtime.index_clients[artwork_type]
    res = index.query(
        namespace=req.namespace,
        vector=vec,
        top_k=req.top_k,
        include_metadata=req.include_metadata,
    )
    return QueryResponse(
        embedding_mode=runtime.mode,
        index=index_name(runtime.prefix, runtime.mode, artwork_type),
        results=res,
    )


def _load_image_bytes(req: QueryRequest) -> bytes:
    if req.image_data_url:
        b, _mime = data_url_to_bytes(req.image_data_url)
        return _validate_image_bytes(b)
    if req.image_url:
        _assert_safe_remote_image_url(req.image_url)
        with httpx.Client(timeout=30.0, follow_redirects=False) as client:
            with client.stream("GET", req.image_url) as r:
                if 300 <= r.status_code < 400:
                    raise HTTPException(
                        status_code=400,
                        detail="Redirects are not allowed for image_url",
                    )
                r.raise_for_status()

                content_length = r.headers.get("content-length")
                if content_length:
                    try:
                        if int(content_length) > MAX_REMOTE_IMAGE_BYTES:
                            raise HTTPException(
                                status_code=413,
                                detail="image_url response is too large",
                            )
                    except ValueError:
                        pass

                data = bytearray()
                for chunk in r.iter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_REMOTE_IMAGE_BYTES:
                        raise HTTPException(
                            status_code=413,
                            detail="image_url response is too large",
                        )
                return _validate_image_bytes(bytes(data))
    raise HTTPException(status_code=400, detail="Provide image_url or image_data_url")


def _assert_safe_remote_image_url(image_url: str) -> None:
    parsed = urlsplit(image_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(
            status_code=400,
            detail="image_url must use http or https and include a hostname",
        )

    hostname = parsed.hostname.strip().lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise HTTPException(
            status_code=400,
            detail="image_url must not target private or loopback addresses",
        )

    try:
        addrinfo = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HTTPException(status_code=400, detail="Unable to resolve image_url host") from exc

    for family, _socktype, _proto, _canonname, sockaddr in addrinfo:
        if family == socket.AF_UNSPEC:
            continue
        ip = ipaddress.ip_address(sockaddr[0])
        if _is_blocked_ip_address(ip):
            raise HTTPException(
                status_code=400,
                detail="image_url must not target private or loopback addresses",
            )


def _is_blocked_ip_address(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_reserved,
            ip.is_multicast,
            ip.is_unspecified,
        )
    )


def _validate_image_bytes(data: bytes) -> bytes:
    try:
        with Image.open(BytesIO(data)) as img:
            img.verify()
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="image_url must point to a valid image"
        ) from exc
    return data


def _stable_dumps(obj: Dict[str, Any]) -> str:
    """Serialize to a stable JSON string for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _json_to_text(obj: Dict[str, Any], max_chars: int = 800) -> str:
    lines = []
    lines.append(f"type: {obj.get('type', '')}")
    lines.append(f"schema_version: {obj.get('schema_version', '')}")
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
