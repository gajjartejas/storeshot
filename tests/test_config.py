"""Unit tests for configuration, color parsing, theme tokens, and JSON config."""

import json
from pathlib import Path
import pytest
from storeshot.config import (
    StoreShotConfig,
    THEMES,
    load_json_config,
    normalize_config_key,
    parse_color,
    parse_csv_colors,
    parse_csv_ints,
)


def test_parse_color_hex_formats():
    assert parse_color("#FFF") == (255, 255, 255, 255)
    assert parse_color("#000") == (0, 0, 0, 255)
    assert parse_color("#FF0000") == (255, 0, 0, 255)
    assert parse_color("#00FF0080") == (0, 255, 0, 128)
    assert parse_color("#1E1B4B") == (30, 27, 75, 255)
    assert parse_color("#00000000") == (0, 0, 0, 0)
    assert parse_color("none") == (0, 0, 0, 0)
    assert parse_color("transparent") == (0, 0, 0, 0)
    assert parse_color(None) == (0, 0, 0, 0)


def test_parse_color_rgb_rgba():
    assert parse_color("rgb(100, 150, 200)") == (100, 150, 200, 255)
    assert parse_color("rgba(10, 20, 30, 0.5)") == (10, 20, 30, 128)
    assert parse_color("rgba(10, 20, 30, 255)") == (10, 20, 30, 255)


def test_parse_color_invalid():
    with pytest.raises(ValueError):
        parse_color("#GGGGGG")
    with pytest.raises(ValueError):
        parse_color("invalid_color_string")
    with pytest.raises(ValueError):
        parse_color("#12345")


def test_parse_csv_helpers():
    assert parse_csv_ints("2, 4, 6, 8", 4) == (2, 4, 6, 8)
    with pytest.raises(ValueError):
        parse_csv_ints("2, 4", 4)
    with pytest.raises(ValueError):
        parse_csv_ints("2, a, 4, 5", 4)

    colors = parse_csv_colors("#FFF, #000, #F00, none", 4)
    assert len(colors) == 4
    assert colors[0] == (255, 255, 255, 255)
    assert colors[1] == (0, 0, 0, 255)
    assert colors[3] == (0, 0, 0, 0)


def test_theme_antigravity_tokens():
    cfg = StoreShotConfig()
    cfg.apply_theme("antigravity")

    assert cfg.theme == "antigravity"
    assert cfg.bg_color_1 == THEMES["antigravity"]["bg_color_1"]
    assert cfg.bg_color_2 == THEMES["antigravity"]["bg_color_2"]
    assert cfg.screenshot_border_width == 3
    assert cfg.screenshot_border_color == "#818CF8"
    assert cfg.screenshot_border_radius == 36
    assert cfg.shadow_blur == 48
    assert cfg.shadow_offset_y == 28


def test_config_validation():
    cfg = StoreShotConfig(
        out_width=1080, out_height=1920, pad_left=600, pad_right=600
    )
    with pytest.raises(ValueError, match="pad-left .* must be less than out-width"):
        cfg.validate()

    cfg2 = StoreShotConfig(
        out_width=1080, out_height=1920, pad_top=1000, pad_bottom=1000
    )
    with pytest.raises(ValueError, match="pad-top .* must be less than out-height"):
        cfg2.validate()

    cfg3 = StoreShotConfig(
        out_width=300, out_height=300,
        pad_left=60, pad_right=60, pad_top=60, pad_bottom=60
    )
    with pytest.raises(ValueError, match="smaller than 200px"):
        cfg3.validate()

    cfg3.force = True
    cfg3.validate()


def test_normalize_config_key():
    assert normalize_config_key("out-width") == "out_width"
    assert normalize_config_key("outWidth") == "out_width"
    assert normalize_config_key("screenshot_border_radius") == "screenshot_border_radius"
    assert normalize_config_key("bgColor1") == "bg_color_1"


def test_load_json_config_root_and_child_inheritance(tmp_path: Path):
    json_path = tmp_path / "input.json"
    data = {
        "theme": "antigravity",
        "out_width": 1200,
        "out_height": 2000,
        "pad_top": 150,
        "screenshots": [
            {
                "file": "1.png",
                "text": "Screenshot One"
            },
            {
                "file": "2.png",
                "text": "Screenshot Two",
                "pad_top": 180,
                "bg_color_1": "#FF0000"
            }
        ]
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    root_cfg, items = load_json_config(json_path)
    assert root_cfg.theme == "antigravity"
    assert root_cfg.out_width == 1200
    assert root_cfg.out_height == 2000
    assert root_cfg.pad_top == 150
    assert len(items) == 2

    # Test child 1 inherits root pad_top and theme
    child1_cfg = root_cfg.merge_child(items[0])
    assert child1_cfg.theme == "antigravity"
    assert child1_cfg.pad_top == 150
    assert child1_cfg.text == "Screenshot One"

    # Test child 2 overrides pad_top and bg_color_1
    child2_cfg = root_cfg.merge_child(items[1])
    assert child2_cfg.theme == "antigravity"
    assert child2_cfg.pad_top == 180
    assert child2_cfg.bg_color_1 == "#FF0000"
    assert child2_cfg.text == "Screenshot Two"


def test_load_json_config_project_relative_paths(tmp_path: Path):
    proj_dir = tmp_path / "project1" / "input"
    proj_dir.mkdir(parents=True)
    json_path = proj_dir / "config.json"
    data = {
        "output_dir": "../output",
        "screenshots": [{"file": "1.png"}]
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    root_cfg, items = load_json_config(json_path)
    assert root_cfg.input_dir == proj_dir
    assert root_cfg.output_dir == (tmp_path / "project1" / "output").resolve()
