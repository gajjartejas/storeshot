"""Unit tests for the CLI interface and flag behavior."""

import json
from pathlib import Path
from click.testing import CliRunner
from PIL import Image

from storeshot.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Produce Play Store / App Store listing-ready graphics" in result.output
    assert "--theme" in result.output
    assert "--config" in result.output
    assert "--dry-run" in result.output
    assert "--fit" in result.output


def test_cli_dry_run(tmp_path: Path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()

    img = Image.new("RGBA", (500, 1000), (100, 150, 200, 255))
    img.save(in_dir / "1.png")

    runner = CliRunner()
    result = runner.invoke(main, [
        "--input", str(in_dir),
        "--output", str(out_dir),
        "--dry-run"
    ])

    assert result.exit_code == 0
    assert "dry_run=True" in result.output
    assert not (out_dir / "1.png").exists()


def test_cli_theme_antigravity(tmp_path: Path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()

    img = Image.new("RGBA", (500, 1000), (100, 150, 200, 255))
    img.save(in_dir / "1.png")

    runner = CliRunner()
    result = runner.invoke(main, [
        "--input", str(in_dir),
        "--output", str(out_dir),
        "--theme", "antigravity",
        "--text", "Antigravity Showcase"
    ])

    assert result.exit_code == 0
    assert (out_dir / "1.png").is_file()


def test_cli_config_json(tmp_path: Path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()

    img1 = Image.new("RGBA", (500, 1000), (100, 150, 200, 255))
    img1.save(in_dir / "screen1.png")
    img2 = Image.new("RGBA", (500, 1000), (200, 100, 150, 255))
    img2.save(in_dir / "screen2.png")

    config_path = tmp_path / "input.json"
    config_data = {
        "theme": "antigravity",
        "input_dir": str(in_dir),
        "output_dir": str(out_dir),
        "screenshots": [
            {
                "file": "screen1.png",
                "text": "Screen One Headline"
            },
            {
                "file": "screen2.png",
                "text": "Screen Two Headline",
                "bg_color_1": "#3B82F6"
            }
        ]
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f)

    runner = CliRunner()
    result = runner.invoke(main, [
        "--config", str(config_path)
    ])

    assert result.exit_code == 0
    assert (out_dir / "screen1.png").is_file()
    assert (out_dir / "screen2.png").is_file()


def test_cli_invalid_padding(tmp_path: Path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()

    runner = CliRunner()
    result = runner.invoke(main, [
        "--input", str(in_dir),
        "--output", str(out_dir),
        "--pad-left", "800",
        "--pad-right", "800",
        "--out-width", "1080"
    ])

    assert result.exit_code != 0
