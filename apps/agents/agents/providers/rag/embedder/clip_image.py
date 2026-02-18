from typing import List

import numpy as np

from PIL import Image
import io

from sentence_transformers import SentenceTransformer


class ClipImageEmbedder:
    """Local CLIP embedder via sentence-transformers.

    Requires:
      - torch
      - sentence-transformers

    Install: pip install -r requirements-image.txt
    """

    def __init__(self, model_name: str = "clip-ViT-B-32", device: str = "cpu") -> None:
        self.model = SentenceTransformer(model_name, device=device)
        # sentence-transformers CLIP image embeddings dim is model-specific; infer by encoding a dummy image.
        dummy = Image.new("RGB", (32, 32), color=(255, 255, 255))
        v = self.model.encode([dummy], convert_to_numpy=True, normalize_embeddings=True)
        self._dim = int(v.shape[1])

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_image(self, image_bytes: bytes) -> List[float]:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        v = self.model.encode([img], convert_to_numpy=True, normalize_embeddings=True)[0]
        return v.astype(np.float32).tolist()

    def embed_texts(self, texts):  # pragma: no cover
        raise NotImplementedError("ClipImageEmbedder only supports image embeddings.")
