# SPDX-License-Identifier: GPL-3.0-only
"""Turn a local JPEG/PNG into a new UGC item using an existing island model.

The MIT TL-UGC-Editor codec encodes the images; ShareMii supplies the item
schema. Nothing here generates a 3D model or initializes a model from a photo.
"""
import io
from pathlib import Path
import warnings

from PIL import Image, ImageOps
import zstandard

import photo_texture_codec as texture
import ugc_import as ugc

MAX_PIXELS = 32 * 1024**2
FITS = ("contain", "cover", "stretch")


def open_image(data):
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in ("JPEG", "PNG"):
                raise ValueError("Choose an actual JPEG or PNG image, not a renamed file.")
            if image.width * image.height > MAX_PIXELS or max(image.size) > 16384:
                raise ValueError("Photo exceeds 32 megapixels or a 16,384 pixel edge. Resize it first.")
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError("Choose a still PNG/JPEG rather than an animated image.")
            image.load()
            return ImageOps.exif_transpose(image).convert("RGBA")


def fit_image(image, size, fit):
    # Crop before resizing: prevents extreme aspect ratios from allocating a
    # huge intermediate image in the original codec's 'cover' implementation.
    if fit == "cover":
        return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
    if fit == "contain":
        return ImageOps.pad(image, size, method=Image.Resampling.LANCZOS, color=(0, 0, 0, 0))
    if fit == "stretch":
        return image.resize(size, Image.Resampling.LANCZOS)
    raise ValueError("Unsupported photo fit. Choose contain, cover or stretch.")


def encoded_size(fmt):
    gobs = texture.div_round_up(fmt.sw_w * fmt.bpe, 64)
    rows = texture.div_round_up(fmt.sw_h, 8 * fmt.bh) * 8 * fmt.bh
    return gobs * rows * 64


def texture_formats(save, template, kind):
    from mii_import import bounded_read, validate_paint
    result = []
    for path in ugc.paths(save, template, kind):
        data = bounded_read(path)
        validate_paint(data)
        raw = zstandard.ZstdDecompressor().decompress(data, max_output_size=64 * 1024**2, allow_extra_data=False)
        fmt = texture.infer_format(path, raw)
        if len(raw) != encoded_size(fmt):
            raise ValueError(f"Unsupported model texture layout: {path.name}. Choose another model.")
        result.append(fmt)
    return result


def name_bytes(name):
    text = ""
    for char in name:
        if len((text + char).encode("utf-16-le")) > 126:
            break
        text += char
    return (text or "Photo").encode("utf-16-le").ljust(128, b"\0")


def convert(codec, save, entry, data):
    """Produce an ordinary ShareMii creation in memory; never modify the model."""
    kind, template = entry["kind"] - 1, entry["template"]
    player, table, attrs, names, vector, vector2 = ugc.schema(codec, save, template, kind)
    from mii_import import span, validate_paint
    enabled = span(player, table, ugc.ENABLE[kind], template * 4) + (template - 1) * 4
    if player[enabled:enabled + 4] != bytes.fromhex("f4ad7f1d"):
        raise ValueError("Create and save a model in Palette House for this category first.")
    formats = texture_formats(save, template, kind)
    image = open_image(data)
    index = template - 1
    metadata = bytearray((kind, 0, 0, 0))
    for field, at in enumerate(attrs):
        if field == ugc.NIGHT[kind]:
            metadata += bytes(((player[at + index // 8] >> (index % 8)) & 1, 0, 0, 0))
        else:
            metadata += player[at + index * 4:at + (index + 1) * 4]
    metadata += player[vector + index * 12:vector + (index + 1) * 12] if vector else bytes(12)
    metadata += player[vector2 + index * 8:vector2 + (index + 1) * 8] if vector2 else bytes(8)
    metadata += b"\xa2" * 4
    label = name_bytes(Path(entry["file"]).stem)
    metadata += label + label
    if kind == 2:
        for i, width in ((2, 64), (3, 128)):
            at = names[i]
            metadata += player[at + index * width:at + (index + 1) * width]
    for marker, fmt in zip((0xa3, 0xa4, 0xa5), formats):
        fitted = fit_image(image, (fmt.px_w, fmt.px_h), entry["fit"])
        encoded = texture.encode_texture(fitted, fmt, "stretch")
        validate_paint(encoded)
        raw = zstandard.ZstdDecompressor().decompress(encoded)
        if len(raw) != encoded_size(fmt):
            raise ValueError("Converted photo texture did not match the model's layout.")
        metadata += bytes((marker,)) * 4 + encoded
    result = bytes(metadata)
    ugc.parse(result, kind)
    return result
