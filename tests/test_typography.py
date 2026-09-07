"""Unit tests for typography, text measurement, and 2-line truncation."""

from PIL import Image, ImageFont
from storeshot.typography import (
    measure_text_lines,
    render_text_block,
    resolve_font,
    wrap_text_to_2_lines,
)


def test_font_resolution():
    font, desc = resolve_font(None, size=28)
    assert font is not None
    assert isinstance(desc, str)

    # Test preset family keywords and bold weights
    for fam in ("sans", "serif", "mono", "georgia", "arial"):
        f_reg, d_reg = resolve_font(fam, size=28, weight="regular")
        assert f_reg is not None
        f_bold, d_bold = resolve_font(fam, size=28, weight="bold")
        assert f_bold is not None


def test_wrap_single_line():
    font = ImageFont.load_default(size=24)
    text = "Short text"
    lines = wrap_text_to_2_lines(text, font, max_width=400)
    assert len(lines) == 1
    assert lines[0] == "Short text"


def test_wrap_two_lines():
    font = ImageFont.load_default(size=24)
    text = "This is a longer line of text that wraps cleanly"
    lines = wrap_text_to_2_lines(text, font, max_width=300)
    assert len(lines) == 2
    assert not lines[1].endswith("...")


def test_wrap_and_truncate_three_plus_lines():
    font = ImageFont.load_default(size=24)
    text = (
        "First long line of text followed by second line of text and then a third line "
        "that should definitely overflow and get truncated with ellipsis"
    )
    lines = wrap_text_to_2_lines(text, font, max_width=300)
    assert len(lines) == 2
    assert lines[1].endswith("...")
    assert font.getlength(lines[1]) <= 300


def test_explicit_newline_handling():
    font = ImageFont.load_default(size=24)
    text = "Header Title\nSubtitle description"
    lines = wrap_text_to_2_lines(text, font, max_width=400)
    assert len(lines) == 2
    assert lines[0] == "Header Title"
    assert lines[1] == "Subtitle description"


def test_vertical_line_spacing_measurement():
    font = ImageFont.load_default(size=24)
    lines = ["Line 1", "Line 2"]
    _, h1, _ = measure_text_lines(lines, font, line_height_multiplier=1.0, line_spacing=0)
    _, h2, _ = measure_text_lines(lines, font, line_height_multiplier=1.0, line_spacing=20)
    assert h2 == h1 + 20


def test_render_text_with_pill_and_alignments():
    canvas = Image.new("RGBA", (500, 300), (0, 0, 0, 0))
    font = ImageFont.load_default(size=24)
    lines = ["Smart Analytics", "Track growth in real-time"]

    # Test center alignment
    render_text_block(
        canvas=canvas,
        lines=lines,
        font=font,
        text_color=(255, 255, 255, 255),
        center_x=250,
        top_y=50,
        text_bg=(30, 27, 75, 200),
        align="center",
        line_spacing=12
    )
    px = canvas.getpixel((250, 50))
    assert px[3] > 0

    # Test left alignment
    render_text_block(
        canvas=canvas,
        lines=lines,
        font=font,
        text_color=(255, 255, 255, 255),
        center_x=250,
        top_y=150,
        align="left",
        margin_x=30
    )
    assert canvas.getpixel((30, 150))[3] >= 0
