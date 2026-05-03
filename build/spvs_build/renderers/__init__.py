"""Renderer registry. Each renderer: (controls, out_path) -> None."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from spvs_build.model import Control
from spvs_build.renderers import csv_baseline

Renderer = Callable[[list[Control], Path], None]

RENDERERS: dict[str, Renderer] = {
    "csv-baseline": csv_baseline.render,
}
