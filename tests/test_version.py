"""Ensure runtime version matches the single source in pyproject.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pyai_caching


def test_version_matches_pyproject() -> None:
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as f:
        expected = tomllib.load(f)["project"]["version"]
    assert pyai_caching.__version__ == expected
