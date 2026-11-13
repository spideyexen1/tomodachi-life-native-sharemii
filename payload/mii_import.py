# SPDX-License-Identifier: GPL-3.0-only
"""Apply a reviewed mixed ShareMii queue off-line, then resume the native game automatically.

The pinned ShareMii codecs run against a private copy without Tk. The UGC
adapter verifies its source and corrects the documented vector write.
The existing save-transfer transaction commits the whole batch or preserves the
previous save. No emulator, game package, key, upload or network is involved.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import redirect_stdout
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
import traceback

import save_transfer
import session_lock
import ugc_import

ROOT = Path(__file__).resolve().parents[1]
VENDOR_SHA256 = "19e2a4e75162bbb1fc840ca362318a98db54b3315277ceb758f990e3129a41a3"
MAX_MII_BYTES = 64 * 1024**2
PERSONAL = (0x43CD364F, 0xCD8DBAF8, 0x25B48224, 0x607BA160, 0x68E1134E,
            0x4913AE1A, 0x141EE086, 0x07B9D175, 0x81CF470A, 0x4D78E262,
            0xFBC3FFB0, 0x236E2D73, 0xF3C3DE59, 0x660C5247, 0x5D7D3F45,
            0xAB8AE08B, 0x2545E583, 0x6CF484F4)
PAINT = (0x4C9819E4, 0xDECC8954, 0x23135BC5, 0xFFC750B6, 0xA56E42EC)


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def fields(data: bytes) -> dict[int, int]:
    if len(data) < 0x20 or u32(data, 0) != 0x01020304:
        raise ValueError("Unsupported or incomplete game save.")
    heap = u32(data, 8)
    if heap < 0x20 or heap > len(data) or (heap - 0x20) % 8:
        raise ValueError("Invalid game save entry table.")
    result = {}
    for at in range(0x20, heap, 8):
        key, offset = struct.unpack_from("<II", data, at)
        if not key or not offset:  # schema entries without stored data
            continue
        if key in result:
            raise ValueError("Invalid or duplicate game save field.")
        # The pinned vendor locates hashes by their first occurrence. Refuse a
        # save where that would disagree with the validated entry table.
        if data.find(struct.pack("<I", key)) != at:
            raise ValueError("Ambiguous game save field.")
        result[key] = offset
    return result


def span(data: bytes, table: dict[int, int], key: int, size: int) -> int:
    offset = table.get(key)
    if offset is None or offset < u32(data, 8) or offset + 4 + size > len(data):
        raise ValueError("A required Mii save field is missing or truncated.")
    return offset + 4


def validate_save(save: Path, slots: list[int]) -> None:
    mii, player = (save / "Mii.sav").read_bytes(), (save / "Player.sav").read_bytes()
    mt, pt = fields(mii), fields(player)
    raw = span(mii, mt, 0x881CA27A, 70 * 156)
    for key, size in ((0x2499BFDA, 70 * 64), (0x3A5EDA05, 70 * 128),
                      (0x5E32ADF4, 70 * 4), (0xDFC82223, 27), (0x9999B7D9, 70 * 4)):
        span(mii, mt, key, size)
    for key in PERSONAL:
        span(mii, mt, key, 70 * 4)
    for key in PAINT:
        span(player, pt, key, 71 * 4)
    span(player, pt, 0x114EFF89, 152)
    for slot in slots:
        record = mii[raw + (slot - 1) * 156:raw + slot * 156]
        if u32(record, 0) != 152 or sum(record) == 152:
            raise ValueError(f"Resident slot {slot} is empty. Create a resident in the game first.")


def bounded_read(path: Path) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(MAX_MII_BYTES + 1)
    if len(data) > MAX_MII_BYTES:
        raise ValueError("A Mii or face-paint file exceeds 64 MiB.")
    return data


def validate_mii(data: bytes, sidecars: dict[str, bytes]) -> None:
    if not data or data[0] not in (1, 2, 3):
        raise ValueError("Choose a ShareMii .ltd file (version 1, 2 or 3).")
    minimum = {1: 161, 2: 428, 3: 428}[data[0]]
    if len(data) < minimum:
        raise ValueError("The Mii file is truncated.")
    raw = data[4:160] if data[0] == 3 else data[5:161]
    if len(raw) != 156 or u32(raw, 0) != 152:
        raise ValueError("Invalid Mii appearance record.")
    if data[0] == 3:
        if data[1:3] not in (b"\0\0", b"\1\1"):
            raise ValueError("Incomplete embedded face paint.")
        for start, end in ((232, 296), (296, 424)):
            text = data[start:end].decode("utf-16-le", errors="strict")
            if "\0" not in text:
                raise ValueError("The Mii name or pronunciation is not terminated.")
        if any(bit not in (0, 1) for bit in data[424:427]):
            raise ValueError("Invalid Mii preference data.")
        if data[1:3] == b"\1\1":
            first, last = data.find(b"\xa3" * 4, 428), data.rfind(b"\xa4" * 4)
            if first != 428 or last <= first + 4 or last + 4 >= len(data):
                raise ValueError("Embedded face paint is truncated.")
            validate_paint(data[first + 4:last])
            validate_paint(data[last + 4:])
    if sidecars and set(sidecars) != {".canvas.zs", ".ugctex.zs"}:
        raise ValueError("Both face-paint sidecar files are required.")
    for paint in sidecars.values():
        validate_paint(paint)


def validate_paint(data: bytes) -> None:
    import zstandard
    if not data or len(data) > MAX_MII_BYTES:
        raise ValueError("Invalid face-paint size.")
    try:
        declared = zstandard.frame_content_size(data)
        if declared not in (zstandard.CONTENTSIZE_UNKNOWN, zstandard.CONTENTSIZE_ERROR) and declared > MAX_MII_BYTES:
            raise ValueError("Expanded face paint exceeds 64 MiB.")
        expanded = zstandard.ZstdDecompressor().decompress(data, max_output_size=MAX_MII_BYTES + 1, allow_extra_data=False)
    except zstandard.ZstdError as error:
        raise ValueError("Invalid or truncated compressed creation texture.") from error
    if len(expanded) > MAX_MII_BYTES:
        raise ValueError("Expanded face paint exceeds 64 MiB.")



def load_vendor(source: Path):
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != VENDOR_SHA256:
        raise ValueError("ShareMii source verification failed. Repair the integration first.")
    wanted = {"trimStr", "offsetLocator", "DecodeSexuality", "EncodeSexuality", "ShareMii"}
    tree = ast.parse(data, filename=str(source))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    if {node.name for node in nodes} != wanted:
        raise ValueError("Unsupported ShareMii source.")
    namespace = dict(os=os, re=re, shutil=shutil, struct=struct, stat=stat, Path=Path, datetime=datetime)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)
    return namespace["ShareMii"]


def check_entries(entries: list[dict]) -> None:
    if not isinstance(entries, list) or not 1 <= len(entries) <= 70:
        raise ValueError("The import queue must contain 1 to 70 creations.")
    slots = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Invalid import queue entry.")
        kind = entry.get("kind", 0)
        if type(kind) is not int or not 0 <= kind <= 7:
            raise ValueError("Invalid creation category.")
        maximum = 70 if kind == 0 else ugc_import.LIMITS[kind - 1]
        if type(entry.get("slot")) is not int or not 1 <= entry["slot"] <= maximum:
            raise ValueError("Invalid resident slot in import queue.")
        if not isinstance(entry.get("file"), str) or Path(entry["file"]).suffix.lower() != ((".ltd",) + ugc_import.EXTENSIONS)[kind]:
            raise ValueError("Choose a local ShareMii file matching its category.")
        slots.append((kind, entry["slot"]))
    if len(slots) != len(set(slots)):
        raise ValueError("Each creation needs a different destination within its category (different destination resident for Miis).")


def apply_batch(port: Path, entries: list[dict], operation=None) -> dict:
    check_entries(entries)
    port, userdata, backups = save_transfer.port_paths(port)
    operation = operation or (load_vendor(port / "integration" / "ShareMii" / "ShareMii.py") if any(e.get("kind", 0) == 0 for e in entries) else None)
    ugc = ugc_import.load_vendor(port / "integration" / "ShareMii" / "ShareUGC.py") if any(e.get("kind", 0) for e in entries) else None
    with save_transfer.transfer_session(port, userdata):
        save_transfer.recover_pending(userdata, backups)
        current = userdata / "save"
        validate_save(current, [entry["slot"] for entry in entries if not entry.get("kind", 0)])
        before = save_transfer.inventory(current)
        with tempfile.TemporaryDirectory(prefix="mii-batch-", dir=port / "build") as temporary:
            temporary = Path(temporary)
            staged = temporary / "save"
            staged.mkdir()
            save_transfer.copy_snapshot(current, staged, before)
            # Snapshot and validate every input before calling the vendor once.
            inputs = []
            for index, entry in enumerate(entries):
                original = Path(entry["file"])
                data = bounded_read(original)
                kind = entry.get("kind", 0)
                sidecars = {suffix: bounded_read(Path(str(original) + suffix))
                            for suffix in (".canvas.zs", ".ugctex.zs") if Path(str(original) + suffix).is_file()}
                if kind:
                    ugc_import.preflight(ugc, current, entry["slot"], kind - 1, data)
                else:
                    validate_mii(data, sidecars)
                extension = ((".ltd",) + ugc_import.EXTENSIONS)[kind]
                target = temporary / f"input-{index}{extension}"
                target.write_bytes(data)
                for suffix, paint in sidecars.items():
                    Path(str(target) + suffix).write_bytes(paint)
                inputs.append(target)
            (staged / "Ugc").mkdir(exist_ok=True)
            with redirect_stdout(io.StringIO()):
                for entry, source in zip(entries, inputs):
                    kind = entry.get("kind", 0)
                    if kind:
                        ugc("Import", entry["slot"], str(staged), str(source), True, kind - 1)
                        ugc_import.verify(ugc, staged, entry["slot"], kind - 1, source.read_bytes())
                    else:
                        operation("Import", entry["slot"], str(staged), str(source), False)
            validate_save(staged, [entry["slot"] for entry in entries if not entry.get("kind", 0)])
            output = (staged / "Mii.sav").read_bytes()
            table = fields(output)
            raw_at = span(output, table, 0x881CA27A, 70 * 156)
            names_at = span(output, table, 0x2499BFDA, 70 * 64)
            for entry, source in zip(entries, inputs):
                if entry.get("kind", 0):
                    ugc_import.verify(ugc, staged, entry["slot"], entry["kind"] - 1, source.read_bytes())
                    continue
                data = source.read_bytes()
                if data[0] != 3:
                    continue  # older formats are converted by the pinned vendor
                expected = bytearray(data[4:160])
                if data[1:3] == b"\1\1" or Path(str(source) + ".canvas.zs").is_file():
                    expected[43] = 1
                index = entry["slot"] - 1
                if (output[raw_at + index * 156:raw_at + (index + 1) * 156] != expected or
                    output[names_at + index * 64:names_at + (index + 1) * 64] != data[232:296]):
                    raise ValueError("An imported Mii did not pass read-back verification.")
            for name in ("Mii.sav", "Player.sav", "Map.sav"):
                if (staged / name).stat().st_size != (current / name).stat().st_size:
                    raise ValueError("Import changed a save's structure; the previous save was preserved.")
            if save_transfer.digest(staged / "Map.sav") != before["Map.sav"]:
                raise ValueError("Import unexpectedly changed the island map.")
            if save_transfer.inventory(current) != before:
                raise ValueError("The active save changed while preparing the batch.")
            info = save_transfer.inspect_root(staged)
            result = save_transfer.replace_snapshot(userdata, backups, staged, info)
            result["miis"] = sum(not e.get("kind", 0) for e in entries)
            result["creations"] = len(entries)
            return result


def resume(port: Path) -> None:
    python = port / "deps" / "python-venv" / "Scripts" / "pythonw.exe"
    subprocess.Popen([str(python), str(port / "integration" / "play-native.py")], cwd=port)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--parent-pid", type=int, required=True)
    args = parser.parse_args()
    closed = False
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        if request.get("schema") != 1 or Path(request.get("save", "")).resolve() != (ROOT / "build" / "userdata" / "save").resolve():
            raise ValueError("Unsupported import request or save location.")
        check_entries(request.get("entries"))
        from bridge import wait_for_game
        wait_for_game(args.parent_pid)
        closed = True
        deadline = time.monotonic() + 10
        while session_lock.active(ROOT / "integration" / "game-session.json"):
            if time.monotonic() >= deadline:
                raise RuntimeError("The previous game launcher has not released the save yet.")
            time.sleep(0.05)
        result = apply_batch(ROOT, request["entries"])
        try:
            save_transfer.atomic_json(ROOT / "integration" / "last-mii-import.json", {"ok": True, **result})
        except OSError:
            pass  # a summary failure must not turn a completed commit into an import error
        resume(ROOT)
        return 0
    except Exception as error:
        try:
            (ROOT / "integration" / "mii-import-error.log").write_text(traceback.format_exc(), encoding="utf-8")
            save_transfer.atomic_json(ROOT / "integration" / "last-mii-import.json", {"ok": False, "error": str(error)})
        except OSError:
            pass
        import ctypes
        language = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3ff
        explanation = {
            0x10: "Importazione interrotta. Backup: build/saves/imports. Il gioco riparte se il salvataggio e disponibile.",
            0x07: "Import unterbrochen. Sicherungen: build/saves/imports. Das Spiel startet bei verfuegbarem Spielstand neu.",
            0x0a: "Importacion interrumpida. Copias: build/saves/imports. El juego vuelve a abrirse si el guardado esta disponible.",
            0x0c: "Import interrompu. Sauvegardes : build/saves/imports. Le jeu redemarre si la sauvegarde est disponible.",
            0x16: "Importacao interrompida. Copias: build/saves/imports. O jogo reabre se o salvamento estiver disponivel.",
        }.get(language, "Import interrupted. Backups: build/saves/imports. The game restarts if the save is available.")
        ctypes.windll.user32.MessageBoxW(None, str(error) + "\n\n" + explanation, "ShareMii", 0x10)
        if closed and not (ROOT / "build" / "userdata" / ".save-import.pending.json").exists():
            resume(ROOT)
        return 1
    finally:
        # The private ticket contains local paths only and is no longer needed.
        if args.request.resolve().parent == (ROOT / "integration").resolve() and args.request.name.startswith("mii-request-"):
            args.request.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
