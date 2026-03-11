from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_mypy_can_typecheck_src_and_tests_without_duplicate_conftest_modules() -> None:
    env = os.environ.copy()
    env.setdefault("UV_CACHE_DIR", str(REPO_ROOT / ".cache" / "uv"))

    result = subprocess.run(
        ["uv", "run", "--no-sync", "python", "-m", "mypy", "src", "tests"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_test_tree_has_explicit_package_markers_for_namespace_stability() -> None:
    assert (REPO_ROOT / "tests" / "__init__.py").is_file()
    assert (REPO_ROOT / "tests" / "unit" / "__init__.py").is_file()
    assert (REPO_ROOT / "tests" / "integration" / "__init__.py").is_file()
    assert (REPO_ROOT / "tests" / "pipeline" / "__init__.py").is_file()
