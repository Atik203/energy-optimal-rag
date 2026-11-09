"""Command-line interface.

Standard library only. ``validate`` is functional; the experiment subcommands
are explicit stubs that exit non-zero until their phase is implemented.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rag_energy import __version__
from rag_energy.config import REPO_ROOT, validate_all

_STUB_TEXT = (
    "{name}: not implemented in v0.1.0. This is an intentional scaffold stub. "
    "See docs/IMPLEMENTATION_PLAN.md for the phase that implements it, and "
    "ROADMAP.md for the gate that must pass first."
)


def _cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else REPO_ROOT
    report = validate_all(root)
    print(f"Validating {report.n_files} config file(s) under {root / 'configs'}")
    for path in report.files:
        rel = path.relative_to(root)
        if str(rel) in report.errors:
            print(f"FAIL {rel}")
        else:
            print(f"OK   {rel}")
    if report.errors:
        print("\nErrors:")
        for name, problems in report.errors.items():
            for problem in problems:
                print(f"  - {name}: {problem}")
        return 1
    print("\nAll configs valid.")
    return 0


def _cmd_stub(name: str) -> int:
    print(_STUB_TEXT.format(name=name), file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rag-energy",
        description="Energy-optimal retrieval depth research harness (project G2).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    validate = subparsers.add_parser(
        "validate",
        help="Parse all TOML configs and check required keys.",
    )
    validate.add_argument(
        "--root",
        default=None,
        help="Repository root (default: inferred from the installed package).",
    )
    validate.set_defaults(func=_cmd_validate)

    prepare = subparsers.add_parser("prepare", help="Prepare and chunk a dataset (stub).")
    prepare.add_argument("--config", default=None, help="Run config path.")
    prepare.set_defaults(func=lambda _args: _cmd_stub("prepare"))

    run = subparsers.add_parser("run", help="Run a depth sweep (stub).")
    run.add_argument("--config", default=None, help="Run config path.")
    run.set_defaults(func=lambda _args: _cmd_stub("run"))

    blocks = subparsers.add_parser("blocks", help="Run block energy calibration (stub).")
    blocks.add_argument("--config", default=None, help="Run config path.")
    blocks.set_defaults(func=lambda _args: _cmd_stub("blocks"))

    analyze = subparsers.add_parser("analyze", help="Analyze a completed run (stub).")
    analyze.add_argument("--run-id", default=None, help="Registered run identifier.")
    analyze.set_defaults(func=lambda _args: _cmd_stub("analyze"))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
