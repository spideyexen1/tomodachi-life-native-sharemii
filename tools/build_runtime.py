# SPDX-License-Identifier: GPL-3.0-only
"""Rebuild the open-source host; do not recompile or redistribute game code."""
from pathlib import Path
import os
import subprocess


def build(port: Path, python: Path) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("RECOMP_", "SSBU_", "TOMO_"))}
    env.update({
        "RECOMP_CLANG": str(port / "deps" / "llvm" / "bin" / "clang.exe"),
        "SDL3_ROOT": str(port / "deps" / "SDL3"),
        "VULKAN_HEADERS": str(port / "deps" / "Vulkan-Headers"),
        "IMGUI_ROOT": str(port / "deps" / "imgui"),
        "FFMPEG_ROOT": str(port / "deps" / "ffmpeg"),
        "RECOMP_EXE": "tomodachi_sharemii.exe",
        "RECOMP_DLL": "tomodachi_game.dll",
        "RECOMP_BIN": str(port / "build" / "binaries" / "1.0.4"),
        "SUYU_ROOT": str(port / "deps" / "suyu"),
        "PYTHONUNBUFFERED": "1",
    })
    work = port / "build" / "work"
    for script, output in (("gen_sdktest.py", "sdktest_data.h"), ("gen_quad_tests.py", "quad_tests.h")):
        if not (work / output).exists():
            subprocess.run([str(python), script], cwd=work, env=env, check=True)
    subprocess.run([str(python), "build.py", "host"], cwd=work, env=env, check=True)
    if not (work / "tomodachi_sharemii.exe").is_file():
        raise RuntimeError("The custom host executable was not produced.")
