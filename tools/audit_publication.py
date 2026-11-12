# SPDX-License-Identifier: GPL-3.0-only
"""Audit tracked source files before publishing; never inspect the game install."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".nsp", ".nsz", ".xci", ".nca", ".nup", ".rom", ".3ds", ".cia", ".keys", ".tik", ".cert", ".sav", ".ltd", ".ltdx", ".zs", ".elf", ".exe", ".dll", ".so", ".dylib", ".obj", ".lib", ".pdb", ".bin", ".zip", ".rar", ".7z", ".torrent", ".log", ".png", ".jpg", ".ico"}
FORBIDDEN_DIRS = {"build", "deps", "romfs", "exefs", "userdata", "saves", "backups", "vendor", "__pycache__", "scambi"}
ALLOWED_SUFFIXES = {".py", ".h", ".json", ".md", ".txt", ".yml", ".yaml"}
ALLOWED_NAMES = {"LICENSE", ".gitignore", ".gitattributes"}
PATTERNS = (
    ("credential-like token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("console key value", re.compile(r"(?im)^\s*(?:master_key_[0-9a-f]+|header_key|titlekek_[0-9a-f]+|key_area_key_\w+)\s*=\s*[0-9a-f]{32,}\s*$")),
    ("personal Windows home path", re.compile(r"(?i)[A-Z]:[\\/]Users[\\/][A-Za-z0-9_.-]+")),
    ("game-package download link", re.compile(r"https?://[^\s<>\"']+\.(?:nsp|nsz|xci|nca|nup|torrent)(?:\?[^\s<>\"']*)?", re.I)),
)


def audit(root: Path = ROOT) -> list[str]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    paths = [Path(name) for name in result.stdout.decode("utf-8").split("\0") if name]
    if not paths:
        return ["No tracked files found; stage the intended source files first."]
    failures = []
    for relative in paths:
        file = root / relative
        suffix = file.suffix.lower()
        if suffix in FORBIDDEN_SUFFIXES or any(part.lower() in FORBIDDEN_DIRS for part in relative.parts[:-1]):
            failures.append(f"Forbidden artifact: {relative}")
            continue
        if relative.name not in ALLOWED_NAMES and suffix not in ALLOWED_SUFFIXES:
            failures.append(f"Unrecognized publication file: {relative}")
            continue
        if file.is_symlink() or file.stat().st_size > 1_000_000:
            failures.append(f"Symlink or oversized file: {relative}")
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeError:
            failures.append(f"Non-text file: {relative}")
            continue
        for description, pattern in PATTERNS:
            if pattern.search(text):
                failures.append(f"{description}: {relative}")
    print(f"Audited {len(paths)} tracked files.")
    return failures


if __name__ == "__main__":
    errors = audit()
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print("PASS: source/documentation only; no detected game artifacts, credentials or personal paths.")
    raise SystemExit(bool(errors))
