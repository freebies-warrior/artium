from __future__ import annotations

import time

from pinecone import Pinecone, ServerlessSpec


def index_name(prefix: str, embedding_mode: str, artwork_type: str) -> str:
    # Pinecone requires lowercase alphanumeric and '-' only; replace underscores with hyphens
    return f"{prefix}-{embedding_mode}-{artwork_type}".lower().replace("_", "-")


def ensure_index(
    *,
    pc: Pinecone,
    name: str,
    dimension: int,
    metric: str,
    cloud: str,
    region: str,
    wait_ready: bool = True,
) -> None:
    existing = set(pc.list_indexes().names())
    if name in existing:
        return

    pc.create_index(
        name=name,
        dimension=int(dimension),
        metric=metric,
        spec=ServerlessSpec(cloud=cloud, region=region),
    )

    if wait_ready:
        for _ in range(60):
            desc = pc.describe_index(name)
            status = getattr(desc, "status", None)
            if status and status.get("ready"):
                return
            time.sleep(2)


def get_index(pc: Pinecone, name: str):
    """Return an Index client targeted at the given index name.

    Pinecone SDKs may require the index host, so we derive it from describe_index.
    """
    desc = pc.describe_index(name)
    host = getattr(desc, "host", None) or (desc.get("host") if isinstance(desc, dict) else None)
    if not host:
        raise ValueError(f"Could not determine host for index '{name}'. Describe result: {desc}")
    return pc.Index(host=host)


def build_pinecone_client(api_key: str) -> Pinecone:
    return Pinecone(api_key=api_key)
