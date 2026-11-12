# SPDX-License-Identifier: GPL-3.0-only
"""Build the Windows wizard from tracked source only; no game installation is read."""
import argparse
import hashlib
import io
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "Tomodachi-Life-Native-ShareMii-Setup.exe"


def make_bundle() -> bytes:
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.decode().split("\0")
    selected = [name for name in tracked if name and (name.startswith(("payload/", "tools/", "docs/")) or name in ("LICENSE", "NOTICE.md", "README.md", "README.it.md", "requirements-integration.txt"))]
    required = {"tools/setup_backend.py", "tools/setup-lock.json", "tools/install_integration.py", "payload/bridge.py", "payload/friday_sharemii.h", "payload/save_transfer.py", "tools/repair_menu.py", "tools/menu_config.py", "tools/patch_texture_lifetime.py"} | {"payload/locales/" + code + ".json" for code in ("de", "es", "fr", "pt")}
    if not required.issubset(selected):
        raise ValueError("Stage the setup source before building its source-only bundle.")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(selected):
            path = ROOT / name
            if path.suffix.lower() not in {".py", ".h", ".json", ".md", ".txt"} and name != "LICENSE":
                raise ValueError("Unexpected bundle file: " + name)
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument("--compiler", type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python", str(ROOT / "tools" / "audit_publication.py")], cwd=ROOT, check=True)
    bundle = make_bundle()
    resource = out / "setup-sources.zip"
    resource.write_bytes(bundle)
    digest = out / "setup-sources.sha256"
    digest.write_text(hashlib.sha256(bundle).hexdigest(), encoding="ascii")
    compiler = args.compiler or Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe"
    executable = out / NAME
    subprocess.run([str(compiler), "/nologo", "/target:winexe", "/platform:x64", "/optimize+", "/out:" + str(executable), "/win32manifest:" + str(ROOT / "setup" / "app.manifest"), "/resource:" + str(resource) + ",SetupSources", "/resource:" + str(digest) + ",SetupSourcesHash", "/r:System.Windows.Forms.dll", "/r:System.Drawing.dll", "/r:System.IO.Compression.dll", "/r:System.IO.Compression.FileSystem.dll", "/r:System.Web.Extensions.dll", *(str(file) for file in sorted((ROOT / "setup").glob("*.cs")))], check=True)
    checksum = hashlib.sha256(executable.read_bytes()).hexdigest()
    (out / (NAME + ".sha256")).write_text(checksum + "  " + NAME + "\n", encoding="ascii")
    print(executable)
    print("SHA-256: " + checksum)


if __name__ == "__main__":
    main()
