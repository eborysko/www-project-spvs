"""Command-line interface for spvs-build."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import click

from spvs_build.loader import LoadError, load_supplement
from spvs_build.renderers import RENDERERS
from spvs_build.validator import ValidationError
from spvs_build.validator import validate as run_validate


def _print_errors(errors: list[LoadError | ValidationError]) -> None:
    for e in errors:
        loc = e.file or "<unknown>"
        if getattr(e, "line", None) is not None:
            loc += f":{e.line}"
        click.echo(f"{loc}\n  {e.code} [{e.code[0]}] {e.message}", err=True)


@click.group()
def main() -> None:
    """SPVS YAML build tooling."""


@main.command()
@click.option("--supplement", type=click.Path(path_type=Path), required=True)
@click.option("--schema", type=click.Path(path_type=Path), required=True)
def validate(supplement: Path, schema: Path) -> None:
    """Validate a supplement directory against the schema and semantic rules."""
    schema_doc = json.loads(schema.read_text())
    controls, load_errors = load_supplement(supplement)
    val_errors = run_validate(controls, schema_doc)
    errors = list(load_errors) + list(val_errors)
    if errors:
        _print_errors(errors)
        click.echo(f"\n{len(errors)} error(s) in supplement {supplement}", err=True)
        sys.exit(1)
    click.echo(f"{len(controls)} controls validated cleanly.")


@main.command()
@click.option("--supplement", type=click.Path(path_type=Path), required=True)
@click.option("--schema", type=click.Path(path_type=Path), required=True)
@click.option("--renderer", type=click.Choice(list(RENDERERS.keys())), required=True)
@click.option("--out", type=click.Path(path_type=Path), required=True)
def build(supplement: Path, schema: Path, renderer: str, out: Path) -> None:
    """Validate then render the supplement to the specified output."""
    schema_doc = json.loads(schema.read_text())
    controls, load_errors = load_supplement(supplement)
    val_errors = run_validate(controls, schema_doc)
    errors = list(load_errors) + list(val_errors)
    if errors:
        _print_errors(errors)
        sys.exit(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    RENDERERS[renderer](controls, out)
    click.echo(f"Wrote {out} ({len(controls)} controls, renderer={renderer}).")


@main.command()
@click.option("--supplement", type=click.Path(path_type=Path), required=True)
@click.option("--schema", type=click.Path(path_type=Path), required=True)
@click.option("--renderer", type=click.Choice(list(RENDERERS.keys())), required=True)
@click.option("--out", type=click.Path(path_type=Path), required=True)
def check(supplement: Path, schema: Path, renderer: str, out: Path) -> None:
    """Build, then verify the rendered output matches what's committed (drift check)."""
    ctx = click.get_current_context()
    ctx.invoke(build, supplement=supplement, schema=schema, renderer=renderer, out=out)
    result = subprocess.run(
        [  # noqa: S603,S607 (controlled args, no shell=True)
            "git",
            "diff",
            "--exit-code",
            "--",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        click.echo(result.stdout)
        click.echo(
            f"\nDrift detected in {out}. The committed file does not match what "
            "your YAML produces. Regenerate locally and commit:\n"
            f"  uv run python -m spvs_build build --supplement {supplement} "
            f"--schema {schema} --renderer {renderer} --out {out}",
            err=True,
        )
        sys.exit(1)
    click.echo(f"{out} is in sync with sources.")


@main.command()
@click.option("--csv", "csv_path", type=click.Path(path_type=Path, exists=True), required=True)
@click.option("--out", type=click.Path(path_type=Path), required=True)
def migrate(csv_path: Path, out: Path) -> None:
    """One-shot conversion of a baseline CSV into per-control YAML files."""
    from spvs_build.migrate import migrate_baseline  # type: ignore[import-untyped]

    out.mkdir(parents=True, exist_ok=True)
    errors = migrate_baseline(csv_path, out)
    if errors:
        for e in errors:
            click.echo(f"row {e.csv_row}: {e.message}", err=True)
        click.echo(f"\n{len(errors)} migration error(s) - fix the CSV and re-run.", err=True)
        sys.exit(1)
    n_files = sum(1 for _ in out.rglob("*.yaml"))
    click.echo(f"Migrated {n_files} controls to {out}.")


if __name__ == "__main__":
    main()
