# SPDX-License-Identifier: GPL-3.0-only
"""Exercise the actual stable-title helper with and without a launcher override."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "friday_activity_title.h"
static void title_env(const char *value) {
#ifdef _WIN32
    _putenv_s("TOMO_DISCORD_TITLE", value ? value : "");
#else
    if (value) setenv("TOMO_DISCORD_TITLE", value, 1);
    else unsetenv("TOMO_DISCORD_TITLE");
#endif
}
int main(void) {
    const char *diagnostic = "game - frame 9000 - 60 fps";
    title_env(NULL);
    assert(friday_activity_title(diagnostic) == diagnostic);
    title_env("");
    assert(friday_activity_title(diagnostic) == diagnostic);
    title_env("Tomodachi Life: Living the Dream");
    assert(!strcmp(friday_activity_title(diagnostic), "Tomodachi Life: Living the Dream"));
    assert(!strcmp(friday_activity_title("loading resources"), "Tomodachi Life: Living the Dream"));
    title_env(NULL);
    assert(!strcmp(friday_activity_title("room code: EXAMPLE"), "room code: EXAMPLE"));
    puts("PASS: stable activity/loading titles; diagnostic fallback without an override.");
    return 0;
}
'''


def main():
    compiler = shutil.which("gcc") or shutil.which("clang")
    if not compiler:
        raise RuntimeError("GCC or Clang is required for this development check.")
    with tempfile.TemporaryDirectory(prefix="activity-title-check-") as temporary:
        source, executable = Path(temporary) / "check.c", Path(temporary) / "check.exe"
        source.write_text(HARNESS, encoding="utf-8")
        subprocess.run([compiler, "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "payload"), str(source), "-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
