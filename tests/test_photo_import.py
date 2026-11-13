# SPDX-License-Identifier: GPL-3.0-only
import io
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "payload"))
from PIL import Image
import photo_import as photos
import photo_texture_codec as texture
import mii_import as mi


def image_bytes(image, format="PNG", **options):
    out = io.BytesIO()
    image.save(out, format=format, **options)
    return out.getvalue()


class PhotoInputs(unittest.TestCase):
    def test_jpeg_png_and_exif_rotation(self):
        source = Image.new("RGB", (3, 5), "red")
        self.assertEqual(photos.open_image(image_bytes(source)).size, (3, 5))
        exif = Image.Exif()
        exif[274] = 6
        self.assertEqual(photos.open_image(image_bytes(source, "JPEG", exif=exif)).size, (5, 3))

    def test_renamed_other_format_corrupt_and_oversize_are_refused(self):
        with self.assertRaisesRegex(ValueError, "actual JPEG or PNG"):
            photos.open_image(image_bytes(Image.new("RGB", (2, 2)), "GIF"))
        with self.assertRaises(Exception):
            photos.open_image(b"not an image")
        with self.assertRaisesRegex(ValueError, "16,384"):
            photos.open_image(image_bytes(Image.new("RGB", (16385, 1))))

    def test_three_fits_keep_dimensions_and_contain_transparency(self):
        source = Image.new("RGBA", (8, 2), "red")
        contain = photos.fit_image(source, (8, 8), "contain")
        self.assertEqual(contain.getpixel((4, 0))[3], 0)
        self.assertEqual(contain.getpixel((4, 4)), (255, 0, 0, 255))
        for fit in ("cover", "stretch"):
            self.assertEqual(photos.fit_image(source, (8, 8), fit).getpixel((0, 0)), (255, 0, 0, 255))
        # Crop first avoids a massive intermediate for thin images.
        self.assertEqual(photos.fit_image(Image.new("RGB", (1, 16384)), (256, 256), "cover").size, (256, 256))

    def test_unicode_names_remain_terminated_without_split_surrogates(self):
        data = photos.name_bytes("A" * 62 + "\U0001f600")
        self.assertEqual(len(data), 128)
        self.assertEqual(data.decode("utf-16-le").split("\0")[0], "A" * 62)

    def test_photo_ticket_needs_item_model_and_fit(self):
        entry = {"kind": 6, "slot": 2, "file": "photo.JPG", "photo": True, "template": 1, "fit": "contain"}
        mi.check_entries([entry])
        for changed in ({"kind": 0}, {"template": 0}, {"fit": "unknown"}, {"photo": 1}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                mi.check_entries([{**entry, **changed}])

    def test_block_linear_swizzle_round_trip(self):
        for w, h, bpe, block in ((256, 256, 4, 16), (96, 96, 8, 16), (128, 128, 8, 16), (64, 64, 16, 8)):
            with self.subTest(width=w, height=h):
                raw = bytes((i * 31 + i // 256) % 256 for i in range(w * h * bpe))
                swizzled = texture.swizzle_block_linear(raw, w, h, bpe, block)
                self.assertEqual(texture.deswizzle_block_linear(swizzled, w, h, bpe, block), raw)

    def test_bc1_bc3_color_and_alpha(self):
        source = Image.new("RGBA", (4, 4), (255, 0, 0, 255))
        source.putpixel((0, 0), (0, 0, 0, 0))
        for encode, decode in ((texture.bc1_encode, texture.bc1_decode), (texture.bc3_encode, texture.bc3_decode)):
            out = decode(encode(source.tobytes(), 4, 4), 4, 4)
            self.assertEqual(out[3], 0)
            self.assertGreater(out[4], 240)
            self.assertEqual(out[7], 255)


if __name__ == "__main__":
    unittest.main()
