"""The `tended` command: births an instance from the bundled kernel."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def kernel_root() -> Path:
    if (HERE / "tools" / "brain.py").exists():
        return HERE
    checkout = HERE.parent
    if (checkout / "tools" / "brain.py").exists():
        return checkout
    raise SystemExit("tended: no kernel found next to this package")


def version() -> str:
    return (kernel_root() / "VERSION").read_text().strip()


def init(args: argparse.Namespace) -> int:
    root = kernel_root()
    cmd = [sys.executable, str(root / "tools" / "brain.py"), "init",
           args.path, "--full"]
    if args.org:
        cmd += ["--org", args.org]
    if args.force:
        cmd.append("--force")
    env = {**os.environ, "BRAIN_DIR": str(root), "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(cmd, env=env).returncode


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="tended",
        description="Birth a tended knowledge base. Everything else runs "
                    "inside the instance with python3 tools/brain.py.")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="verb")
    p = sub.add_parser("init", help="create a full instance in <dir>")
    p.add_argument("path")
    p.add_argument("--org", default="")
    p.add_argument("--force", action="store_true")
    if argv and argv[0] not in ("init", "--version", "-h", "--help"):
        print(f"tended only creates instances. Run `{argv[0]}` inside an "
              f"instance with: python3 tools/brain.py {argv[0]}",
              file=sys.stderr)
        return 2
    args = parser.parse_args(argv)
    if args.version:
        print(f"tended {version()}")
        return 0
    if args.verb == "init":
        return init(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
