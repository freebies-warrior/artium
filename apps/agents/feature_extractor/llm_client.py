from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from PIL import Image

from core.settings import get_settings
from utils.parsing import parse_json_object

logger = logging.getLogger(__name__)


class VisionLLMClient:
    def __init__(self, model: str = "gemini-2.5-flash-image") -> None:
        api_key = get_settings().GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not configured")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _img_part(self, img, mime_type: str = "image/jpeg") -> types.Part:
        # If it's already a PIL image
        if isinstance(img, Image.Image):
            buf = io.BytesIO()
            img.save(buf, "JPEG")  # use positional format (works across pillow variants)
            return types.Part.from_bytes(data=buf.getvalue(), mime_type=mime_type)

        # If it's some object with a .save(fp) method (google image types, etc.)
        buf = io.BytesIO()
        img.save(buf)  # no format kw
        data = buf.getvalue()

        # sniff header -> choose mime
        if data.startswith(b"\x89PNG"):
            mt = "image/png"
        elif data.startswith(b"\xff\xd8"):
            mt = "image/jpeg"
        else:
            mt = mime_type

        return types.Part.from_bytes(data=data, mime_type=mt)

    def _img_part_from_bytes(self, data: bytes, mime_type: str = "image/jpeg") -> types.Part:
        if data.startswith(b"\x89PNG"):
            mime_type = "image/png"
        elif data.startswith(b"\xff\xd8"):
            mime_type = "image/jpeg"
        return types.Part.from_bytes(data=data, mime_type=mime_type)

    def generate_json(
        self,
        prompt: str,
        image_jpeg_bytes: Optional[bytes] = None,
        images_jpeg_bytes: Optional[List[bytes]] = None,
    ) -> Dict[str, Any]:
        contents = [prompt]
        if images_jpeg_bytes:
            contents.extend([self._img_part_from_bytes(b) for b in images_jpeg_bytes])
        elif image_jpeg_bytes is not None:
            contents.append(self._img_part_from_bytes(image_jpeg_bytes))

        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )
        except Exception:
            logger.exception(
                "llm request failed",
                extra={
                    "provider": "gemini",
                    "model": self.model,
                    "step": "feature_extractor.generate_json",
                },
            )
            raise

        try:
            return parse_json_object(resp.text, source="feature_extractor.generate_json")
        except ValueError:
            logger.exception(
                "llm response parsing failed",
                extra={
                    "provider": "gemini",
                    "model": self.model,
                    "step": "feature_extractor.generate_json",
                },
            )
            raise

    def generate_text(
        self,
        prompt: str,
        image_jpeg_bytes: Optional[bytes] = None,
        images_jpeg_bytes: Optional[List[bytes]] = None,
    ) -> str:
        """Generate plain text response (not JSON)."""
        contents = [prompt]
        if images_jpeg_bytes:
            contents.extend([self._img_part_from_bytes(b) for b in images_jpeg_bytes])
        elif image_jpeg_bytes is not None:
            contents.append(self._img_part_from_bytes(image_jpeg_bytes))

        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )
        except Exception:
            logger.exception(
                "llm request failed",
                extra={
                    "provider": "gemini",
                    "model": self.model,
                    "step": "feature_extractor.generate_text",
                },
            )
            raise
        return (resp.text or "").strip()

    def edit_image(
        self, model: str, prompt: str, room: Image.Image, art: Image.Image | None = None
    ) -> Image.Image:
        contents = [prompt, self._img_part(room)]
        if art is not None:
            contents.append(self._img_part(art))

        try:
            resp = self.client.models.generate_content(model=model, contents=contents)
        except Exception:
            logger.exception(
                "llm request failed",
                extra={
                    "provider": "gemini",
                    "model": model,
                    "step": "feature_extractor.edit_image",
                },
            )
            raise

        for part in resp.parts or []:
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None) is not None:
                data = inline.data  # bytes
                img = Image.open(io.BytesIO(data))
                # normalize
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                return img

        raise RuntimeError("No inline image returned from Gemini.")


class GeminiVisionClient(VisionLLMClient):
    def __init__(self, model: str = "gemini-2.5-flash-image") -> None:
        self.client = VisionLLMClient(model=model)

    def infer_json(self, prompt: str, image_bytes: bytes) -> Dict[str, Any]:
        return self.client.generate_json(prompt=prompt, image_jpeg_bytes=image_bytes)

    def infer_text(self, prompt: str, image_bytes: bytes) -> str:
        return self.client.generate_text(prompt=prompt, image_jpeg_bytes=image_bytes)
