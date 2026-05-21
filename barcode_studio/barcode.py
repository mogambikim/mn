from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from PIL import Image
import pdf417gen


CODE128_PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312", "132212", "221213",
    "221312", "231212", "112232", "122132", "122231", "113222", "123122", "123221", "223211", "221132",
    "221231", "213212", "223112", "312131", "311222", "321122", "321221", "312212", "322112", "322211",
    "212123", "212321", "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
    "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121", "313121", "211331",
    "231131", "213113", "213311", "213131", "311123", "311321", "331121", "312113", "312311", "332111",
    "314111", "221411", "431111", "111224", "111422", "121124", "121421", "141122", "141221", "112214",
    "112412", "122114", "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
    "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112", "421211", "212141",
    "214121", "412121", "111143", "111341", "131141", "114113", "114311", "411113", "411311", "113141",
    "114131", "311141", "411131", "211412", "211214", "211232", "2331112",
]


@dataclass(frozen=True)
class BarcodeSettings:
    module_size: float = 5.1
    x: int = 0
    y: int = 0
    width: int | None = 1736
    height: int | None = 396
    canvas_width: int | None = None
    canvas_height: int | None = None
    rotation: str = "none"
    padding: int = 0
    columns: int = 12
    security_level: int = 5

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "BarcodeSettings":
        data = dict(payload or {})
        if data.get("rotation", "none") != "none":
            raise ValueError("Only rotation='none' is supported.")
        return cls(
            module_size=float(data.get("module_size") or cls.module_size),
            x=int(data.get("x") or 0),
            y=int(data.get("y") or 0),
            width=_optional_int(data.get("width"), cls.width),
            height=_optional_int(data.get("height"), cls.height),
            canvas_width=_optional_int(data.get("canvas_width"), None),
            canvas_height=_optional_int(data.get("canvas_height"), None),
            rotation=data.get("rotation", "none"),
            padding=int(data.get("padding") or 0),
            columns=int(data.get("columns") or cls.columns),
            security_level=int(data.get("security_level") or cls.security_level),
        )


def _optional_int(value: Any, default: int | None) -> int | None:
    if value in (None, ""):
        return default
    return int(value)


def render_pdf417(text: str, settings: BarcodeSettings) -> Image.Image:
    codes = pdf417gen.encode(
        text,
        columns=settings.columns,
        security_level=settings.security_level,
    )
    scale = max(1, round(settings.module_size))
    barcode = pdf417gen.render_image(codes, scale=scale, ratio=3, padding=settings.padding).convert("RGB")

    if settings.width and settings.height:
        barcode = barcode.resize((settings.width, settings.height), Image.Resampling.NEAREST)

    if settings.canvas_width and settings.canvas_height:
        canvas = Image.new("RGB", (settings.canvas_width, settings.canvas_height), "white")
        canvas.paste(barcode, (settings.x, settings.y))
        return canvas

    if settings.x or settings.y:
        canvas_w = settings.x + barcode.width
        canvas_h = settings.y + barcode.height
        canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
        canvas.paste(barcode, (settings.x, settings.y))
        return canvas

    return barcode


def render_code128(text: str, width: int = 900, height: int = 180) -> Image.Image:
    value = str(text or "").strip()
    if not value:
        raise ValueError("ICN is required to generate Code 128.")

    codes = [104]
    for char in value:
        code = ord(char) - 32
        if code < 0 or code > 95:
            raise ValueError("Code 128 input must contain printable ASCII characters only.")
        codes.append(code)
    checksum = codes[0] + sum(code * index for index, code in enumerate(codes[1:], start=1))
    codes.extend([checksum % 103, 106])

    modules: list[int] = []
    for code in codes:
        pattern = CODE128_PATTERNS[code]
        for position, width_digit in enumerate(pattern):
            modules.extend([1 if position % 2 == 0 else 0] * int(width_digit))

    quiet = 10
    modules = [0] * quiet + modules + [0] * quiet
    module_width = max(1, width // len(modules))
    barcode_width = len(modules) * module_width
    barcode_height = max(40, int(height * 0.72))
    barcode = Image.new("RGB", (barcode_width, barcode_height), "white")
    pixels = barcode.load()
    for index, module in enumerate(modules):
        if module:
            start = index * module_width
            for x in range(start, start + module_width):
                for y in range(barcode_height):
                    pixels[x, y] = (0, 0, 0)

    canvas = Image.new("RGB", (width, height), "white")
    x = max(0, (width - barcode.width) // 2)
    y = max(0, (height - barcode.height) // 2)
    canvas.paste(barcode, (x, y))
    return canvas


def decode_pdf417(source: str | Path | bytes | BinaryIO) -> str:
    image = _open_image(source)
    try:
        return _decode_with_pyzbar(image)
    except Exception as pyzbar_error:
        try:
            return _decode_with_zxing(image)
        except Exception as zxing_error:
            raise RuntimeError(
                f"Unable to decode PDF417. pyzbar: {pyzbar_error}; zxing: {zxing_error}"
            ) from zxing_error


def _open_image(source: str | Path | bytes | BinaryIO) -> Image.Image:
    if isinstance(source, (str, Path)):
        return Image.open(source).convert("RGB")
    if isinstance(source, bytes):
        return Image.open(io.BytesIO(source)).convert("RGB")
    source.seek(0)
    return Image.open(source).convert("RGB")


def _decode_with_pyzbar(image: Image.Image) -> str:
    from pyzbar.pyzbar import ZBarSymbol, decode

    results = decode(image, symbols=[ZBarSymbol.PDF417])
    if not results:
        raise RuntimeError("No PDF417 barcode found.")
    return results[0].data.decode("utf-8", errors="replace")


def _decode_with_zxing(image: Image.Image) -> str:
    import tempfile
    import zxing

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
        temp_path = Path(temp.name)
        image.save(temp_path, "PNG")

    try:
        reader = zxing.BarCodeReader()
        result = reader.decode(str(temp_path), try_harder=True, possible_formats="PDF_417")
        if not result or not result.parsed:
            raise RuntimeError("No PDF417 barcode found.")
        return result.parsed
    finally:
        temp_path.unlink(missing_ok=True)
