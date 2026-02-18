from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence


class Embedder(ABC):
    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        raise NotImplementedError

    @abstractmethod
    def embed_image(self, image_bytes: bytes) -> List[float]:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError
