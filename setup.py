"""Bundles the kernel manifest into the wheel inside the tended package."""

import ast
import os
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.egg_info import egg_info

ROOT = Path(__file__).resolve().parent
EXTRA_PATHS = ["sources/README.md", "brain.config.yml"]
SKIP_NAMES = ("node_modules", "__pycache__", ".build-cache", "dist",
              ".pytest_cache")
SKIP = shutil.ignore_patterns(*SKIP_NAMES, "*.pyc")


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


class EggInfo(egg_info):
    def find_sources(self):
        super().find_sources()
        for rel in manifest() + EXTRA_PATHS + ["setup.py"]:
            src = ROOT / rel
            if src.is_file():
                self.filelist.append(rel)
                continue
            for dirpath, dirnames, filenames in os.walk(src):
                dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES]
                for name in filenames:
                    if not name.endswith(".pyc"):
                        self.filelist.append(
                            str(Path(dirpath, name).relative_to(ROOT)))


setup(cmdclass={"build_py": BuildPy, "egg_info": EggInfo})
