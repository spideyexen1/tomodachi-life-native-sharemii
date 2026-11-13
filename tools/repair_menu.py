# SPDX-License-Identifier: GPL-3.0-only
"""Recover F1 with a selected renderer profile, without a build or download."""
import argparse
import json
from pathlib import Path
import subprocess

import install_integration as integration
from menu_config import configure


def repair(port: Path, renderer: str = "auto") -> dict:
    integration.validate_port(port)
    integration.refuse_running_game(port)
    return configure(port, renderer)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port-dir", type=Path, required=True)
    parser.add_argument("--renderer", choices=("auto", "opengl", "vulkan"), default="auto")
    args = parser.parse_args()
    try:
        result = repair(args.port_dir.expanduser().resolve(), args.renderer)
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
