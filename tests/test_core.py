"""Unit tests for core image processing, masks, rims, and layouts."""

import json
from pathlib import Path
from PIL import Image
import pytest

from storeshot.config import StoreShotConfig
from storeshot.core import (
    create_rounded_mask,
    draw_canvas_borders,
    draw_stroked_rim,
    process_batch,
    process_single_image,
)


@pytest.fixture
def sample_screenshot(tmp_path: Path) -> Path:
    img_path = tmp_path / "test_screenshot.png"
    img = Image.new("RGBA", (1080, 2400), (40, 60, 90, 255))
    img.save(img_path)
    return img_path


def test_rounded_mask():
    w, h, r = 100, 100, 20
    mask = create_rounded_mask(w, h, r)
    assert mask.size == (w, h)

    # Top-left corner pixel should be 0 (masked out)
    assert mask.getpixel((0, 0)) == 0
    # Center pixel should be 255
    assert mask.getpixel((50, 50)) == 255


def test_canvas_borders():
    canvas = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    widths = (5, 5, 5, 5)
    colors = (
        (255, 0, 0, 255),
        (0, 255, 0, 255),
        (0, 0, 255, 255),
        (255, 255, 0, 255),
    )
    draw_canvas_borders(canvas, widths, colors)

    # Top border pixel
    assert canvas.getpixel((50, 2)) == (255, 0, 0, 255)
    # Right border pixel
    assert canvas.getpixel((98, 50)) == (0, 255, 0, 255)
    # Bottom border pixel
    assert canvas.getpixel((50, 98)) == (0, 0, 255, 255)
    # Left border pixel
    assert canvas.getpixel((2, 50)) == (255, 255, 0, 255)


def test_stroked_rim():
    canvas = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    box = (20, 20, 180, 180)
    stroke_color = (129, 140, 248, 255)  # #818CF8
    draw_stroked_rim(canvas, box, radius=16, stroke_width=4, stroke_color=stroke_color)

    # Top border edge should have stroke color approximate
    px = canvas.getpixel((100, 20))
    assert px[3] > 150
    assert abs(px[0] - stroke_color[0]) <= 20
    assert abs(px[1] - stroke_color[1]) <= 20
    assert abs(px[2] - stroke_color[2]) <= 20


def test_process_single_image_contain(sample_screenshot: Path, tmp_path: Path):
    out_path = tmp_path / "output.png"
    cfg = StoreShotConfig(
        out_width=1080,
        out_height=1920,
        pad_left=40,
        pad_right=40,
        pad_top=120,
        pad_bottom=200,
        screenshot_border_radius=32,
        fit="contain"
    )
    summary = process_single_image(sample_screenshot, out_path, cfg)

    assert out_path.is_file()
    assert summary["output_size"] == [1080, 1920]

    # Inner available space: w=1000, h=1600. Aspect ratio of 1080x2400 is 0.45
    # scaled height should be 1600, scaled width: 1600 * (1080/2400) = 720
    assert summary["scaled_size"][1] == 1600
    assert abs(summary["scaled_size"][0] - 720) <= 2

    # Placement must be centered horizontally: pad_left + (1000 - 720)/2 = 40 + 140 = 180
    assert abs(summary["screenshot_placement"][0] - 180) <= 2
    assert summary["screenshot_placement"][1] == 120

    with Image.open(out_path) as out_img:
        assert out_img.size == (1080, 1920)


def test_process_single_image_cover(sample_screenshot: Path, tmp_path: Path):
    out_path = tmp_path / "output_cover.png"
    cfg = StoreShotConfig(
        out_width=1080,
        out_height=1920,
        pad_left=40,
        pad_right=40,
        pad_top=120,
        pad_bottom=200,
        fit="cover"
    )
    summary = process_single_image(sample_screenshot, out_path, cfg)
    assert summary["scaled_size"] == [1000, 1600]
    assert summary["screenshot_placement"] == [40, 120, 1040, 1720]


def test_process_single_image_jpg(sample_screenshot: Path, tmp_path: Path):
    out_path = tmp_path / "output.jpg"
    cfg = StoreShotConfig(
        format="jpg",
        quality=85
    )
    process_single_image(sample_screenshot, out_path, cfg)
    assert out_path.is_file()
    with Image.open(out_path) as out_img:
        assert out_img.format == "JPEG"
        assert out_img.mode == "RGB"


def test_process_batch_and_template(tmp_path: Path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()

    for i in range(1, 4):
        im = Image.new("RGBA", (500, 1000), (i * 50, 100, 150, 255))
        im.save(in_dir / f"{i}.png")

    template_file = tmp_path / "template.json"
    cfg = StoreShotConfig(
        input_dir=in_dir,
        output_dir=out_dir,
        template=str(template_file),
        theme="antigravity",
        text="Batch Test Title\nSubtitle info"
    )
    successful, failed = process_batch(cfg)

    assert len(successful) == 3
    assert len(failed) == 0
    assert template_file.is_file()

    with open(template_file) as f:
        data = json.load(f)
        assert "config" in data
        assert "sample_layout" in data
        assert data["config"]["theme"] == "antigravity"


def test_process_batch_with_json_items(tmp_path: Path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()

    for i in range(1, 3):
        im = Image.new("RGBA", (500, 1000), (i * 80, 120, 160, 255))
        im.save(in_dir / f"app_{i}.png")

    root_cfg = StoreShotConfig(
        input_dir=in_dir,
        output_dir=out_dir,
        theme="antigravity",
        text_position="bottom"
    )
    items = [
        {
            "file": "app_1.png",
            "text": "App Feature One"
        },
        {
            "file": "app_2.png",
            "text": "App Feature Two",
            "bg_color_1": "#00FF00"
        }
    ]
    successful, failed = process_batch(root_cfg, items=items)

    assert len(failed) == 0
    assert len(successful) == 2
    assert (out_dir / "app_1.png").is_file()
    assert (out_dir / "app_2.png").is_file()
