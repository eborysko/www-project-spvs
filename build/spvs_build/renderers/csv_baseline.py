"""CSV renderer for the 1.0 baseline supplement."""

from __future__ import annotations

import csv
from pathlib import Path

from spvs_build.model import Control

COLUMNS = [
    "category_id",
    "category_name",
    "sub-category_id",
    "sub-category_name",
    "req_id",
    "req_description",
    "level 1",
    "level 2",
    "level 3",
    "NIST",
    "OWASP_CICD_Risk",
    "cwe_mapping",
    "cwe_description",
]


def _id_sort_key(c: Control) -> tuple[int, ...]:
    parts = c.id.lstrip("V").split(".")
    return tuple(int(p) for p in parts)


def _level_marks(level: int) -> tuple[str, str, str]:
    marks = tuple("X" if level == n else "" for n in (1, 2, 3))
    return (marks[0], marks[1], marks[2])


def _format_nist(c: Control) -> str:
    items = c.mappings.get("nist_800_53")
    if not items or not items.items:
        return ""
    ids = ", ".join(i.id for i in items.items)
    return f"NIST 800-53: {ids}"


def _format_owasp_cicd(c: Control) -> str:
    items = c.mappings.get("owasp_cicd")
    if not items or not items.items:
        return ""
    return ";".join(i.id for i in items.items)


def _format_cwe_pair(c: Control) -> tuple[str, str]:
    items = c.mappings.get("cwe")
    if not items or not items.items:
        return "", ""
    ids = ";".join(i.id for i in items.items)
    descs = ";".join(i.description or "" for i in items.items)
    return ids, descs


def render(controls: list[Control], out_path: Path) -> None:
    """Write the baseline 1.0 CSV. Deterministic, byte-identical for same input."""
    sorted_controls = sorted(controls, key=_id_sort_key)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(COLUMNS)
        for c in sorted_controls:
            l1, l2, l3 = _level_marks(c.level)
            cwe_ids, cwe_descs = _format_cwe_pair(c)
            writer.writerow(
                [
                    c.category.id,
                    c.category.name,
                    c.sub_category.id,
                    c.sub_category.name,
                    c.id,
                    c.description.strip().replace("\n", " "),
                    l1,
                    l2,
                    l3,
                    _format_nist(c),
                    _format_owasp_cicd(c),
                    cwe_ids,
                    cwe_descs,
                ]
            )
