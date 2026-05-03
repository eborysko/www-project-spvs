"""One-shot CSV → YAML migration for the baseline supplement."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

CHANGE_TAG_PATTERNS = [
    (re.compile(r"^\[ADDED, SPLIT FROM ([^\]]+)\]\s*"), "ADDED+SPLIT_FROM"),
    (re.compile(r"^\[MODIFIED, MOVED FROM ([^\]]+)\]\s*"), "MODIFIED+MOVED_FROM"),
    (re.compile(r"^\[ADDED\]\s*"), "ADDED"),
    (re.compile(r"^\[MODIFIED\]\s*"), "MODIFIED"),
    (re.compile(r"^\[MOVED FROM ([^\]]+)\]\s*"), "MOVED_FROM"),
    (re.compile(r"^\[MOVED TO ([^\]]+)\]\s*"), "MOVED_TO"),
    (re.compile(r"^\[DELETED, MERGED TO ([^\]]+)\]\s*"), "DELETED_MERGED_TO"),
    (re.compile(r"^\[DELETED\]\s*"), "DELETED"),
    (re.compile(r"^\[LEVEL L([1-3]) > L([1-3])\]\s*"), "LEVEL_CHANGE"),
]

STOPWORDS = {
    "verify",
    "that",
    "is",
    "are",
    "the",
    "a",
    "an",
    "of",
    "for",
    "in",
    "to",
    "and",
    "or",
    "with",
    "by",
    "on",
    "as",
    "be",
}


@dataclass(frozen=True)
class MigrationError:
    csv_row: int
    message: str


def migrate_baseline(csv_path: Path, out_dir: Path) -> list[MigrationError]:
    errors: list[MigrationError] = []
    seen_slugs: dict[str, set[str]] = {}
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.default_flow_style = False
    yaml.width = 200

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            cat_name = row.get("category_name") or row.get("catagory_name", "")
            sub_name = row.get("sub-category_name") or row.get("sub-catagory_name", "")
            req_id = row["req_id"]
            if req_id == "-":
                continue

            doc = _build_doc(row, cat_name, sub_name, row_num, errors)
            if doc is None:
                continue

            slug = _derive_slug(
                doc["description"], seen_slugs.setdefault(row["sub-category_id"], set())
            )
            seen_slugs[row["sub-category_id"]].add(slug)

            sub_id = row["sub-category_id"]
            cat_id = row["category_id"]
            target_dir = out_dir / cat_id / sub_id
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"{req_id}-{slug}.yaml"
            with target.open("w", encoding="utf-8") as out:
                yaml.dump(doc, out)

    return errors


def _build_doc(
    row: dict,  # type: ignore
    cat_name: str,
    sub_name: str,
    row_num: int,
    errors: list,  # type: ignore
) -> dict | None:  # type: ignore
    description, change_tags = _extract_change_tags(row["req_description"])

    cwe_ids = _split(row.get("cwe_mapping", ""), ";")
    cwe_descs = _split(row.get("cwe_description", ""), ";")
    if cwe_ids and len(cwe_ids) != len(cwe_descs):
        errors.append(
            MigrationError(
                row_num,
                f"cwe_mapping has {len(cwe_ids)} ids but cwe_description has "
                f"{len(cwe_descs)}: cannot pair safely. Fix the CSV first.",
            )
        )
        return None

    nist = _parse_nist(row.get("NIST", ""))
    cicd = _split(row.get("OWASP_CICD_Risk", ""), ";")
    level = _detect_level(row)

    mappings: dict = {}  # type: ignore
    if nist:
        mappings["nist_800_53"] = {"items": nist}
    if cicd:
        mappings["owasp_cicd"] = {"items": cicd}
    if cwe_ids:
        mappings["cwe"] = {
            "items": [{"id": i, "description": d} for i, d in zip(cwe_ids, cwe_descs, strict=False)]
        }

    metadata: dict = {"status": "active"}  # type: ignore
    if change_tags:
        metadata["change_tags"] = change_tags

    return {
        "id": row["req_id"],
        "category": {"id": row["category_id"], "name": cat_name},
        "sub_category": {"id": row["sub-category_id"], "name": sub_name},
        "description": LiteralScalarString(description.strip()),
        "level": level,
        "mappings": mappings,
        "metadata": metadata,
    }


def _extract_change_tags(description: str) -> tuple[str, list]:  # type: ignore
    tags: list = []  # type: ignore
    desc = description
    while True:
        matched = False
        for pattern, kind in CHANGE_TAG_PATTERNS:
            m = pattern.match(desc)
            if not m:
                continue
            matched = True
            desc = desc[m.end() :]
            if kind == "MODIFIED+MOVED_FROM":
                tags.append({"type": "MODIFIED"})
                tags.append({"type": "MOVED_FROM", "reference": m.group(1)})
            elif kind == "ADDED+SPLIT_FROM":
                tags.append({"type": "ADDED"})
                tags.append({"type": "SPLIT_FROM", "reference": m.group(1)})
            elif kind == "LEVEL_CHANGE":
                tags.append(
                    {
                        "type": "LEVEL_CHANGE",
                        "from_level": int(m.group(1)),
                        "to_level": int(m.group(2)),
                    }
                )
            elif m.groups():
                tags.append({"type": kind, "reference": m.group(1)})
            else:
                tags.append({"type": kind})
            break
        if not matched:
            break
    return desc, tags


def _parse_nist(raw: str) -> list[str]:
    raw = raw.strip()
    prefix = "NIST 800-53:"
    if raw.startswith(prefix):
        raw = raw[len(prefix) :].strip()
    return [s.strip() for s in raw.split(",") if s.strip()]


def _split(raw: str, sep: str) -> list[str]:
    return [s.strip() for s in raw.split(sep) if s.strip()]


def _detect_level(row: dict) -> int:  # type: ignore
    for n in (1, 2, 3):
        if (row.get(f"level {n}") or "").strip().upper() == "X":
            return n
    return 1


def _derive_slug(description: str, taken: set[str]) -> str:
    words = re.findall(r"[a-z0-9]+", description.lower())
    words = [w for w in words if w not in STOPWORDS][:6]
    slug = "-".join(words)[:60].strip("-") or "control"
    base = slug
    counter = 2
    while slug in taken:
        slug = f"{base}-{counter}"[:60]
        counter += 1
    return slug
