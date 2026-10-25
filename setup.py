"""Bundles the kernel manifest into the wheel inside the tended package."""

import ast
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).resolve().parent
EXTRA_PATHS = ["sources/README.md", "brain.config.yml"]
SKIP = shutil.ignore_patterns(
    "node_modules", "__pycache__", ".build-cache", "dist", "*.pyc",
    ".pytest_cache")


def manifest() -> list[str]:
    tree = ast.parse((ROOT / "tools" / "brain.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", "") == "KERNEL_COPY_PATHS"
                for t in node.targets):
            return list(ast.literal_eval(node.value))
    raise SystemExit("KERNEL_COPY_PATHS not found in tools/brain.py")


class BuildPy(build_py):
    def run(self):
        super().run()
        dest = Path(self.build_lib) / "tended" / "kernel"
        for rel in manifest() + EXTRA_PATHS:
            src, dst = ROOT / rel, dest / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst, symlinks=True, ignore=SKIP)
            else:
                shutil.copyfile(src, dst)


setup(cmdclass={"build_py": BuildPy})
