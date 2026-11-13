# SPDX-License-Identifier: GPL-3.0-only
"""Validated add-only adapter for the pinned original ShareUGC codec.

Format and field layout come from Star-F0rce/ShareMii (GPL-3.0).
Only user creations are read; this module contains no game assets.
"""
import hashlib
from pathlib import Path

SHA256 = "60f70d809b6c79b4358f590b649cd450e197793061d7b8e1b89b6bb7d04f26b7"
EXTENSIONS = (".ltdf", ".ltdc", ".ltdg", ".ltdi", ".ltde", ".ltdo", ".ltdl")
TYPES = ("Food", "Cloth", "Goods", "Interior", "Exterior", "MapObject", "MapFloor")
# The original add codec packs the slot index in one byte. Do not silently
# truncate indices 256..298 in the game's larger clothing array.
LIMITS = (99, 256, 99, 99, 99, 99, 99)
COUNTS = (10, 10, 17, 8, 11, 13, 8)
NIGHT = (5, 6, 13, 4, 7, 9, 4)
ENABLE = (0xF4A39965, 0xAF129C33, 0x1A9C00FE, 0xA39744E9, 0xF4BEADC2, 0x5951050B, 0xA1126D32)
TEX = (0x3558B77F, 0x59BFA9D3, 0x70D10A48, 0xE7F9D439, 0x16227C50, 0xA9C5CFB8, 0x06A7A14C)
HASH = (0x6D48F8E2, 0x89F25CAC, 0x56202100, 0x7FEF7F7D, 0x38D72795, 0x1B28B170, 0x816D50A3)


def load_vendor(path):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("ShareUGC source verification failed. Repair the integration first.")
    namespace = {"__name__": "verified_shareugc"}
    # This pinned module contains only standard-library imports and codec
    # definitions, with no GUI initialization or command-line entry point.
    text = data.decode("utf-8")
    before = "playersav[vOffset+((slot)*8):vOffset+((slot)*8)+8] ="
    after = "playersav[v2Offset+((slot)*8):v2Offset+((slot)*8)+8] ="
    if text.count(before) != 1:
        raise ValueError("Unsupported ShareUGC vector write.")
    # The pinned importer writes MaterialTexScale into the BaseColor/Scale
    # array by mistake. Its export path already reads the separate v2Offset.
    # Correct only that write in memory; keep the verified vendor file intact.
    exec(compile(text.replace(before, after), str(path), "exec"), namespace)
    return namespace["ugcStart"]


def parse(data, kind):
    from mii_import import validate_paint
    if not data or data[0] != kind or data[1:4] != bytes(3):
        raise ValueError("The creation file does not match the selected category.")
    name_marker = 4 + 4 * COUNTS[kind] + 20
    name_start = name_marker + 4
    name_size = 448 if kind == 2 else 256
    canvas_marker = name_start + name_size
    if (len(data) <= canvas_marker + 12 or data.find(b"\xa2" * 4) != name_marker or
            data.find(b"\xa3" * 4) != canvas_marker):
        raise ValueError("Invalid or truncated creation name/header.")
    texture_marker, thumb_marker = data.find(b"\xa4" * 4), data.find(b"\xa5" * 4)
    if not canvas_marker + 4 < texture_marker < thumb_marker - 4 < len(data) - 8:
        raise ValueError("Invalid or truncated creation textures.")
    blocks = (data[canvas_marker + 4:texture_marker], data[texture_marker + 4:thumb_marker], data[thumb_marker + 4:])
    for block in blocks:
        validate_paint(block)
    for start, size in ((name_start, 128), (name_start + 128, 128)):
        if "\0" not in data[start:start + size].decode("utf-16-le", errors="strict"):
            raise ValueError("The creation name is not terminated.")
    if data[4 + NIGHT[kind] * 4] not in (0, 1):
        raise ValueError("Invalid creation lighting flag.")
    return name_start, blocks


def paths(save, slot, kind):
    base = save / "Ugc" / f"Ugc{TYPES[kind]}{slot - 1:03d}"
    return tuple(Path(str(base) + suffix) for suffix in (".canvas.zs", ".ugctex.zs", "_Thumb.ugctex.zs"))


def schema(codec, save, slot, kind):
    from mii_import import fields, span
    player = (save / "Player.sav").read_bytes()
    table = fields(player)
    # Capture the original codec's own schema on an isolated namespace. No
    # monkeypatch of the shared codec and no operation against the save here.
    import types
    namespace = dict(codec.__globals__)
    captured = []
    namespace["offsetLocator"] = lambda data, key: span(data, table, int(key, 16), 0) - 4
    namespace["shareUGC"] = lambda *args: captured.append(args)
    probe = types.FunctionType(codec.__code__, namespace)
    probe("Export", slot, str(save), "unused", True, kind)
    args = captured[0]
    attrs, names, vector, vector2 = args[5:9]
    count = 299 if kind == 1 else 99
    # Validate the entire referenced arrays before the original codec can use
    # Python slices (which would otherwise permit silent truncation/extension).
    def checked(at, length):
        if at < int.from_bytes(player[8:12], "little") or at + length > len(player):
            raise ValueError("Missing or truncated creation save array.")
    for index, at in enumerate(attrs):
        checked(at, (38 if kind == 1 else 13) if index == NIGHT[kind] else count * 4)
    for index, at in enumerate(names):
        checked(at, count * (64 if index == 2 else 128))
    if vector:
        checked(vector, count * 12)
    if vector2:
        checked(vector2, count * 8)
    for key in ENABLE + TEX + HASH:
        span(player, table, key, 0)
    for keys in (ENABLE, TEX, HASH):
        span(player, table, keys[kind], count * 4)
    return player, table, attrs, names, vector, vector2


def preflight(codec, save, slot, kind, data):
    parse(data, kind)
    player, table, *_ = schema(codec, save, slot, kind)
    from mii_import import span
    enabled = span(player, table, ENABLE[kind], slot * 4) + (slot - 1) * 4
    if any(path.exists() for path in paths(save, slot, kind)) or any(player[enabled:enabled + 4]):
        raise ValueError("The destination item slot is occupied. Import into a free slot.")


def verify(codec, save, slot, kind, data):
    from mii_import import span
    name, blocks = parse(data, kind)
    player, table, attrs, names, vector, vector2 = schema(codec, save, slot, kind)
    index = slot - 1
    for i, at in enumerate(attrs):
        if i == NIGHT[kind]:
            ok = (player[at + index // 8] >> (index % 8)) & 1 == data[4 + i * 4]
        else:
            ok = player[at + index * 4:at + (index + 1) * 4] == data[4 + i * 4:8 + i * 4]
        if not ok:
            raise ValueError(f"Creation attribute read-back verification failed: {TYPES[kind]}, attribute {i}.")
    cursor = name
    for i, at in enumerate(names):
        size = 64 if i == 2 else 128
        if player[at + index * size:at + (index + 1) * size] != data[cursor:cursor + size]:
            raise ValueError("Creation name read-back verification failed.")
        cursor += size
    for at, size, source in ((vector, 12, name - 24), (vector2, 8, name - 12)):
        if at and player[at + index * size:at + (index + 1) * size] != data[source:source + size]:
            raise ValueError(f"Creation vector read-back verification failed: {TYPES[kind]}.")
    enabled = span(player, table, ENABLE[kind], slot * 4) + index * 4
    if player[enabled:enabled + 4] != bytes.fromhex("f4ad7f1d"):
        raise ValueError("Creation enable flag was not committed.")
    for path, expected in zip(paths(save, slot, kind), blocks):
        if path.read_bytes() != expected:
            raise ValueError("Creation texture read-back verification failed.")
