"""Tests for the spvs-build CLI."""

import subprocess
from pathlib import Path


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 (test invocation, controlled args)
        ["uv", "run", "python", "-m", "spvs_build", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_validate_succeeds_on_valid_supplement(
    tmp_path: Path, fixture_dir: Path, schema_path: Path
) -> None:
    base = tmp_path / "controls" / "baseline" / "V1" / "V1.1"
    base.mkdir(parents=True)
    (base / "V1.1.1-verify-mfa-enabled.yaml").write_text(
        (fixture_dir / "valid_control.yaml").read_text()
    )

    result = _run(
        "validate",
        "--supplement",
        str(tmp_path / "controls" / "baseline"),
        "--schema",
        str(schema_path),
        cwd=Path(__file__).parents[2],
    )

    assert result.returncode == 0, result.stderr


def test_cli_validate_fails_on_invalid(tmp_path: Path, schema_path: Path) -> None:
    base = tmp_path / "controls" / "baseline" / "V1" / "V1.1"
    base.mkdir(parents=True)
    (base / "V1.1.1-x.yaml").write_text("id: V1.1.1\nlevel: 99\n")

    result = _run(
        "validate",
        "--supplement",
        str(tmp_path / "controls" / "baseline"),
        "--schema",
        str(schema_path),
        cwd=Path(__file__).parents[2],
    )

    assert result.returncode != 0
    assert "error" in (result.stderr + result.stdout).lower()


def test_cli_build_writes_csv(tmp_path: Path, fixture_dir: Path, schema_path: Path) -> None:
    base = tmp_path / "controls" / "baseline" / "V1" / "V1.1"
    base.mkdir(parents=True)
    (base / "V1.1.1-verify-mfa-enabled.yaml").write_text(
        (fixture_dir / "valid_control.yaml").read_text()
    )
    out = tmp_path / "out.csv"

    result = _run(
        "build",
        "--supplement",
        str(tmp_path / "controls" / "baseline"),
        "--schema",
        str(schema_path),
        "--renderer",
        "csv-baseline",
        "--out",
        str(out),
        cwd=Path(__file__).parents[2],
    )

    assert result.returncode == 0, result.stderr
    assert out.exists()
    expected = (fixture_dir / "expected_baseline.csv").read_bytes()
    assert out.read_bytes() == expected
