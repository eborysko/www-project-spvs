"""Three-stage validation: JSON Schema, naming, referential."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from spvs_build.model import Control, Metadata

SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,59}$")
ID_RE = re.compile(r"^V\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class ValidationError:
    file: str | None
    line: int | None
    code: str
    message: str


def validate(controls: list[Control], schema: dict[str, object]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    errors.extend(_schema_validate(controls, schema))
    errors.extend(_naming_validate(controls))
    errors.extend(_referential_validate(controls))
    return errors


def _schema_validate(controls: list[Control], schema: dict[str, object]) -> list[ValidationError]:
    validator = Draft202012Validator(schema)
    out: list[ValidationError] = []
    for c in controls:
        as_dict = _control_to_raw(c)
        for err in validator.iter_errors(as_dict):
            out.append(
                ValidationError(
                    file=c.source_path,
                    line=None,
                    code="E101",
                    message=f"schema: {err.message} at {list(err.path)}",
                )
            )
    return out


def _naming_validate(controls: list[Control]) -> list[ValidationError]:
    out: list[ValidationError] = []
    for c in controls:
        if c.source_path is None:
            continue
        path = Path(c.source_path)
        stem = path.stem
        if "-" in stem:
            id_part, slug = stem.split("-", 1)
        else:
            id_part, slug = stem, ""
        if id_part != c.id:
            out.append(
                ValidationError(
                    file=c.source_path,
                    line=None,
                    code="E201",
                    message=f"filename id prefix '{id_part}' does not match yaml id '{c.id}'",
                )
            )
        if slug and not SLUG_RE.match(slug):
            out.append(
                ValidationError(
                    file=c.source_path,
                    line=None,
                    code="E202",
                    message=f"slug '{slug}' fails regex {SLUG_RE.pattern}",
                )
            )
        if not ID_RE.match(c.id):
            out.append(
                ValidationError(
                    file=c.source_path,
                    line=None,
                    code="E203",
                    message=f"id '{c.id}' does not match {ID_RE.pattern}",
                )
            )
    return out


def _referential_validate(controls: list[Control]) -> list[ValidationError]:
    out: list[ValidationError] = []
    seen: dict[str, str] = {}
    for c in controls:
        if c.id in seen:
            out.append(
                ValidationError(
                    file=c.source_path,
                    line=None,
                    code="E301",
                    message=f"duplicate id '{c.id}' (also at {seen[c.id]})",
                )
            )
        seen[c.id] = c.source_path or "<unknown>"

    all_ids = {c.id for c in controls}
    for c in controls:
        if c.metadata.moved_to and c.metadata.moved_to not in all_ids:
            out.append(
                ValidationError(
                    file=c.source_path,
                    line=None,
                    code="E302",
                    message=f"metadata.moved_to '{c.metadata.moved_to}' has no matching control",
                )
            )
        for tag in c.metadata.change_tags:
            if tag.reference and tag.reference not in all_ids:
                out.append(
                    ValidationError(
                        file=c.source_path,
                        line=None,
                        code="E303",
                        message=(
                            f"change_tags[].reference '{tag.reference}' " "has no matching control"
                        ),
                    )
                )
    return out


def _control_to_raw(c: Control) -> dict[str, object]:
    return {
        "id": c.id,
        "category": asdict(c.category),
        "sub_category": asdict(c.sub_category),
        "description": c.description,
        "level": c.level,
        "mappings": {
            framework: {
                "items": [
                    item.id
                    if (item.description is None and item.note is None)
                    else {k: v for k, v in asdict(item).items() if v is not None}
                    for item in mapping.items
                ]
            }
            for framework, mapping in c.mappings.items()
        },
        "metadata": _metadata_to_raw(c.metadata),
    }


def _metadata_to_raw(m: Metadata) -> dict[str, object]:
    out: dict[str, object] = {"status": m.status}
    if m.change_tags:
        out["change_tags"] = [
            {k: v for k, v in asdict(t).items() if v is not None} for t in m.change_tags
        ]
    for k in ("introduced_in", "last_modified_in", "moved_to", "owner"):
        v = getattr(m, k)
        if v is not None:
            out[k] = v
    return out
