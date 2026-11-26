"""Build a private copy of the GPU guide with the real addresses.

The tracked ``GPU_Server_Guide.tex`` keeps placeholders so the public repository
never publishes a reachable SSH endpoint. This script copies it, substitutes the
real values, compiles, and writes:

    Slides/GPU_Server_Guide.private.pdf   the file to hand to students
    Slides/GPU_Server_Guide.private.tex   intermediate, gitignored

Usage (values are never stored in the script):

    python scripts/84_build_private_guide.py \
        --internal 10.100.110.110 --global-ip 203.0.113.10 --port 110
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "Slides"
SRC = SLIDES / "GPU_Server_Guide.tex"

PLACEHOLDER_INTERNAL = "10.0.0.50"
PLACEHOLDER_GLOBAL = "203.0.113.10"
PLACEHOLDER_PORT = "110"


def main() -> int:
    ap = argparse.ArgumentParser(description="Compile a private guide with real addresses.")
    ap.add_argument("--internal", required=True, help="campus IP, e.g. 10.x.x.x")
    ap.add_argument("--global-ip", required=True, help="public IP for off-campus access")
    ap.add_argument("--port", default="110", help="public SSH port")
    ap.add_argument("--keep-tex", action="store_true", help="keep the substituted .tex")
    args = ap.parse_args()

    if not SRC.is_file():
        raise SystemExit(f"missing {SRC}")

    text = SRC.read_text(encoding="utf-8")
    text = text.replace(PLACEHOLDER_INTERNAL, args.internal)
    text = text.replace(PLACEHOLDER_GLOBAL, args.global_ip)
    text = text.replace(f"Port {PLACEHOLDER_PORT}", f"Port {args.port}")
    text = text.replace(f"-p {PLACEHOLDER_PORT}", f"-p {args.port}")
    text = text.replace(f"-P {PLACEHOLDER_PORT}", f"-P {args.port}")

    # the addresses are real in this build, so fix the placeholder sentence
    text = text.replace(
        "Addresses and passwords below are \\textbf{placeholders}; use the ones issued to you.",
        "Server addresses are the shared GPU server; use the \\textbf{username and password} issued to you.",
    )

    private_tex = SLIDES / "GPU_Server_Guide.private.tex"
    private_tex.write_text(text, encoding="utf-8")

    for _ in range(2):
        run = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", private_tex.name],
            cwd=SLIDES, capture_output=True, text=True,
        )
        if run.returncode != 0 and "Output written" not in run.stdout:
            print(run.stdout[-1500:])
            raise SystemExit("pdflatex failed")

    built = SLIDES / "GPU_Server_Guide.private.pdf"
    if not built.is_file():
        raise SystemExit("pdf was not produced")

    final = SLIDES / "GPU_Server_Guide_for_students.pdf"
    shutil.copyfile(built, final)
    print(f"wrote {final.name}  ({final.stat().st_size // 1024} KB)")
    print(f"internal {args.internal}   external {args.global_ip}:{args.port}")

    if not args.keep_tex:
        private_tex.unlink(missing_ok=True)
        for ext in (".aux", ".log", ".out"):
            (SLIDES / f"GPU_Server_Guide.private{ext}").unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
