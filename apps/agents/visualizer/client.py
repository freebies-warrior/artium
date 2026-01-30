import io
import json
from typing import Any, Dict, Optional, List
from PIL import Image
from google import genai
from google.genai import types

class GeminiClient:
    def __init__(self) -> None:
        self.client = genai.Client()

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

        resp = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        text = (resp.text or "").strip()
        text = text.removeprefix("```json").removeprefix("```").split("```")[0].strip()
        return json.loads(text)
    
    def edit_image(self, model: str, prompt: str, room: Image.Image, art: Image.Image | None = None) -> Image.Image:
        contents = [prompt, self._img_part(room)]
        if art is not None:
            contents.append(self._img_part(art))

        resp = self.client.models.generate_content(model=model, contents=contents)

        for part in (resp.parts or []):
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None) is not None:
                data = inline.data  # bytes
                img = Image.open(io.BytesIO(data))
                # normalize
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                return img

        raise RuntimeError("No inline image returned from Gemini.")
