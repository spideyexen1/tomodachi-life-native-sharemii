# SPDX-License-Identifier: GPL-3.0-only
"""Apply the verified Vulkan workaround while preserving other graphics settings."""
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import uuid


def configure(port: Path, renderer: str = "vulkan") -> dict:
    if renderer not in ("auto", "opengl", "vulkan"):
        raise ValueError("Unknown renderer profile.")
    port = port.resolve()
    config = port / "build" / "config" / "graphics.ini"
    if not config.resolve().is_relative_to(port) or config.is_symlink():
        raise ValueError("Redirected graphics settings are not supported.")
    original = config.read_bytes() if config.exists() else b""
    # Work on bytes: preserve encoding, line endings, comments and unrelated options.
    bom = b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b""
    contents = original[len(bom):]
    newline = b"\r\n" if b"\r\n" in contents else b"\n"
    runtime_renderer = "always_vulkan" if renderer == "vulkan" else renderer
    values = {b"renderer": runtime_renderer.encode("ascii"), b"menu": b"on"}
    if renderer in ("auto", "opengl"):
        # NVIDIA auto-selects OpenGL. Its menu context must draw into the window,
        # avoiding the DXGI shared texture on which it was invisible.
        values.update({b"present_api": b"opengl", b"window": b"windowed"})
    found = set()

    def replace(match):
        key = match[2].lower()
        found.add(key)
        comment = re.search(rb"[;#].*", match[4])
        # Upstream does not strip inline comments: keep them on a separate line.
        note = match[1] + comment[0] + newline if comment else b""
        return note + match[1] + match[2] + match[3] + values[key]

    pattern = rb"(?im)^([ \t]*)(" + b"|".join(values) + rb")([ \t]*=[ \t]*)([^\r\n]*)"
    contents = re.sub(pattern, replace, contents)
    for key, value in values.items():
        if key not in found:
            if contents and not contents.endswith((b"\n", b"\r")):
                contents += newline
            contents += key + b" = " + value + newline
    # Its byte-oriented parser does not strip a UTF-8 BOM from the first key.
    if bom and not contents.startswith((b"\r", b"\n")):
        contents = newline + contents
    updated = bom + contents
    if updated == original:
        return {"changed": False, "config": str(config), "backup": None, "renderer": runtime_renderer}
    config.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    backup = config.with_name("graphics.ini.menu-backup-" + datetime.now().strftime("%Y%m%d_%H%M%S_") + token[:8]) if config.exists() else None
    if backup is not None:
        shutil.copy2(config, backup)
        if backup.read_bytes() != original or config.read_bytes() != original:
            raise ValueError("Graphics settings changed while being backed up. Close the game and retry.")
    temporary = config.with_name(".menu-repair-" + token + ".tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(config)
    finally:
        temporary.unlink(missing_ok=True)
    return {"changed": True, "config": str(config), "backup": str(backup) if backup else None, "renderer": runtime_renderer}
