import logging
import io
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from PIL import Image

from core.settings import get_settings
from core.utils.parsing import parse_json_object

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self) -> None:
        api_key = get_settings().GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not configured")
        self.client = genai.Client(api_key=api_key)

    def _img_part(self, img, mime_type: str = "image/png") -> types.Part:
        # If it's already a PIL image
        if isinstance(img, Image.Image):
            buf = io.BytesIO()
            img.save(buf, "PNG")  # use positional format (works across pillow variants)
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

    def generate_json(
        self,
        model: str,
        prompt: str,
        image: Optional[Image.Image] = None,
        images: Optional[List[Image.Image]] = None,
    ) -> Dict[str, Any]:
        contents = [prompt]
        if images:
            contents.extend([self._img_part(im) for im in images])
        elif image is not None:
            contents.append(self._img_part(image))

        try:
            resp = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
        except Exception as exc:
            logger.error(
                "llm request failed",
                extra={
                    "provider": "gemini",
                    "model": model,
                    "step": "visualizer.generate_json",
                    "error_type": type(exc).__name__,
                },
            )
            raise

        try:
            return parse_json_object(resp.text, source="visualizer.generate_json")
        except ValueError as exc:
            logger.error(
                "llm response parsing failed",
                extra={
                    "provider": "gemini",
                    "model": model,
                    "step": "visualizer.generate_json",
                    "error_type": type(exc).__name__,
                },
            )
            raise

    def edit_image(
        self, model: str, prompt: str, room: Image.Image, art: Image.Image | None = None
    ) -> Image.Image:
        contents = [prompt, self._img_part(room)]
        if art is not None:
            contents.append(self._img_part(art))

        try:
            resp = self.client.models.generate_content(model=model, contents=contents)
        except Exception as exc:
            logger.error(
                "llm request failed",
                extra={
                    "provider": "gemini",
                    "model": model,
                    "step": "visualizer.edit_image",
                    "error_type": type(exc).__name__,
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
