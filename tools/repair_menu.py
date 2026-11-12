# SPDX-License-Identifier: GPL-3.0-only
"""Recover an invisible F1 menu using Vulkan. No build or download is performed."""
import argparse
import json
from pathlib import Path
import subprocess

import install_integration as integration
from menu_config import configure


def repair(port: Path) -> dict:
    integration.validate_port(port)
    integration.refuse_running_game(port)
    return configure(port)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = repair(args.port_dir.expanduser().resolve())
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
