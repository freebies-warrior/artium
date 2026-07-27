from __future__ import annotations

import socket
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

from agents.core.settings import get_settings
from scripts import rag_api


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    rag_api._runtime = None
    yield
    get_settings.cache_clear()
    rag_api._runtime = None


def _dummy_runtime() -> SimpleNamespace:
    return SimpleNamespace(
        mode="feature_text",
        prefix="artium",
        cfg=SimpleNamespace(get=lambda *args, default=None: default),
        text_embedder=None,
        manus=None,
        numeric_embedder=None,
        image_embedder=None,
        index_clients={},
    )


class _FakeResponse:
    def __init__(self, *, chunks: list[bytes], headers: dict[str, str] | None = None) -> None:
        self.status_code = 200
        self.headers = headers or {}
        self._chunks = chunks

    def raise_for_status(self) -> None:
        return None

    def iter_bytes(self):
        yield from self._chunks

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeClient:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    def stream(self, method: str, url: str) -> _FakeResponse:
        return self._response

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _public_getaddrinfo(host: str, *_args, **_kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]


def _png_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (1, 1), "white").save(buf, format="PNG")
    return buf.getvalue()


def test_health_rejects_wrong_internal_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_TOKEN", "expected-token")
    monkeypatch.setattr(rag_api, "_initialize_runtime", lambda: _dummy_runtime())

    with TestClient(rag_api.app, raise_server_exceptions=False) as client:
        response = client.get("/health", headers={"X-Internal-Token": "wrong-token"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid internal token"}


@pytest.mark.parametrize(
    "image_url",
    [
        "http://127.0.0.1/image.png",
        "http://localhost/image.png",
        "http://169.254.169.254/image.png",
    ],
)
def test_query_rejects_private_image_urls(
    monkeypatch: pytest.MonkeyPatch,
    image_url: str,
) -> None:
    monkeypatch.setenv("INTERNAL_TOKEN", "expected-token")
    monkeypatch.setattr(rag_api, "_initialize_runtime", lambda: _dummy_runtime())

    with TestClient(rag_api.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/query",
            headers={"X-Internal-Token": "expected-token"},
            json={
                "artwork_type": "painting",
                "image_url": image_url,
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "image_url must not target private or loopback addresses"
    }


def test_load_image_bytes_rejects_large_remote_responses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rag_api.socket, "getaddrinfo", _public_getaddrinfo)
    response = _FakeResponse(chunks=[b"x" * (rag_api.MAX_REMOTE_IMAGE_BYTES + 1)])
    monkeypatch.setattr(
        rag_api.httpx,
        "Client",
        lambda *args, **kwargs: _FakeClient(response),
    )

    with pytest.raises(HTTPException) as exc:
        rag_api._load_image_bytes(
            rag_api.QueryRequest(
                artwork_type="painting",
                image_url="https://example.com/too-large.png",
            )
        )

    assert exc.value.status_code == 413
    assert exc.value.detail == "image_url response is too large"


def test_load_image_bytes_rejects_non_image_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rag_api.socket, "getaddrinfo", _public_getaddrinfo)
    response = _FakeResponse(chunks=[b"not an image"])
    monkeypatch.setattr(
        rag_api.httpx,
        "Client",
        lambda *args, **kwargs: _FakeClient(response),
    )

    with pytest.raises(HTTPException) as exc:
        rag_api._load_image_bytes(
            rag_api.QueryRequest(
                artwork_type="painting",
                image_url="https://example.com/not-image.png",
            )
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "image_url must point to a valid image"


def test_load_image_bytes_accepts_valid_public_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rag_api.socket, "getaddrinfo", _public_getaddrinfo)
    png_bytes = _png_bytes()
    response = _FakeResponse(chunks=[png_bytes[:5], png_bytes[5:]])
    monkeypatch.setattr(
        rag_api.httpx,
        "Client",
        lambda *args, **kwargs: _FakeClient(response),
    )

    data = rag_api._load_image_bytes(
        rag_api.QueryRequest(
            artwork_type="painting",
            image_url="https://example.com/image.png",
        )
    )

    assert data == png_bytes
