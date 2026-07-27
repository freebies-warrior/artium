from __future__ import annotations

from typing import List, Sequence, Optional

from openai import OpenAI


class OpenAITextEmbedder:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        dimensions: Optional[int] = None,
        encoding_format: str = "float",
    ) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.dimensions = dimensions
        self.encoding_format = encoding_format

    @property
    def dimension(self) -> int:
        # Cannot know without calling; caller should read from config.
        if self.dimensions is None:
            raise ValueError(
                "dimension unknown: set dimensions in config for deterministic index creation"
            )
        return int(self.dimensions)

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        # OpenAI embeddings supports `dimensions` for text-embedding-3* models.
        # https://platform.openai.com/docs/api-reference/embeddings
        kwargs = {}
        if self.dimensions is not None:
            kwargs["dimensions"] = int(self.dimensions)
        resp = self.client.embeddings.create(
            model=self.model,
            input=list(texts),
            encoding_format=self.encoding_format,
            **kwargs,
        )
        return [d.embedding for d in resp.data]

    def embed_image(self, image_bytes: bytes) -> List[float]:
        raise NotImplementedError("OpenAITextEmbedder does not embed images.")
