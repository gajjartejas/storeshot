"""Typography, text wrapping, and font resolution routines for StoreShot."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont

RGBAColor = Tuple[int, int, int, int]
logger = logging.getLogger("storeshot")

# Standard font candidate mappings by family and weight
SYSTEM_FONTS: Dict[str, Dict[str, List[str]]] = {
    "sans": {
        "regular": [
            "/System/Library/Fonts/SFPro.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
        ],
        "bold": [
            "/System/Library/Fonts/SFPro-Bold.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\segoeuib.ttf",
        ],
    },
    "rounded": {
        "regular": [
            "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
            "/Library/Fonts/Arial Rounded Bold.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ],
        "bold": [
            "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
            "/Library/Fonts/Arial Rounded Bold.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
        ],
    },
    "avenir": {
        "regular": [
            "/System/Library/Fonts/Avenir Next.ttc",
            "/System/Library/Fonts/Avenir.ttc",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
        ],
        "bold": [
            "/System/Library/Fonts/Avenir Next.ttc",
            "/System/Library/Fonts/Avenir.ttc",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "C:\\Windows\\Fonts\\segoeuib.ttf",
        ],
    },
    "serif": {
        "regular": [
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "C:\\Windows\\Fonts\\georgia.ttf",
            "C:\\Windows\\Fonts\\times.ttf",
        ],
        "bold": [
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "C:\\Windows\\Fonts\\georgiab.ttf",
            "C:\\Windows\\Fonts\\timesbd.ttf",
        ],
    },
    "mono": {
        "regular": [
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Supplemental/Courier New.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "C:\\Windows\\Fonts\\consola.ttf",
            "C:\\Windows\\Fonts\\cour.ttf",
        ],
        "bold": [
            "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "C:\\Windows\\Fonts\\consolab.ttf",
            "C:\\Windows\\Fonts\\courbd.ttf",
        ],
    }
}


def resolve_font(
    font_path_or_name: Optional[str] = None,
    size: int = 32,
    weight: str = "normal"
) -> Tuple[Union[ImageFont.FreeTypeFont, ImageFont.ImageFont], str]:
    """Resolve ImageFont instance supporting family aliases, weights, and explicit paths."""
    is_bold = (
        str(weight).lower() in ("bold", "b", "heavy", "black", "semibold", "700", "800", "900")
        or (font_path_or_name and "bold" in str(font_path_or_name).lower())
    )

    if font_path_or_name:
        raw_name = str(font_path_or_name).strip()
        path = Path(raw_name)

        # 1. Direct file path
        if path.is_file():
            try:
                font = ImageFont.truetype(str(path), size=size)
                return font, str(path)
            except Exception as e:
                logger.warning(f"Could not load font file '{raw_name}': {e}. Falling back.")

        # Check in system font directories for filename
        for font_dir in (
            Path("/System/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental"),
            Path("/Library/Fonts"),
            Path("C:\\Windows\\Fonts"),
            Path("/usr/share/fonts/truetype"),
        ):
            candidate_path = font_dir / raw_name
            if candidate_path.is_file():
                try:
                    font = ImageFont.truetype(str(candidate_path), size=size)
                    return font, candidate_path.stem
                except Exception:
                    pass

        # 2. Known family keywords
        norm_name = raw_name.lower().replace("-", "").replace("_", "").replace(" ", "")
        family_key = None
        if norm_name in ("serif", "georgia", "times", "timesnewroman"):
            family_key = "serif"
        elif norm_name in (
            "mono", "monospace", "code", "menlo", "courier", "couriernew"
        ):
            family_key = "mono"
        elif norm_name in (
            "rounded", "arialrounded", "arialroundedbold", "arialroundedmtbold", "round"
        ):
            family_key = "rounded"
        elif norm_name in ("avenir", "avenirnext"):
            family_key = "avenir"
        elif norm_name in (
            "sans", "sansserif", "system", "default", "arial", "helvetica",
            "helveticaneue", "sfpro", "roboto", "inter"
        ):
            family_key = "sans"

        if family_key:
            target_list = SYSTEM_FONTS[family_key]["bold" if is_bold else "regular"]
            for candidate in target_list:
                if os.path.exists(candidate):
                    try:
                        font = ImageFont.truetype(candidate, size=size)
                        return font, f"{family_key.capitalize()} ({Path(candidate).stem})"
                    except Exception:
                        continue

        # 3. Try loading font by exact name via system freetype
        try:
            font = ImageFont.truetype(raw_name, size=size)
            return font, raw_name
        except Exception:
            pass

    # 4. Fallback to system sans font (bold or regular)
    fallback_list = SYSTEM_FONTS["sans"]["bold" if is_bold else "regular"]
    for candidate in fallback_list:
        if os.path.exists(candidate):
            try:
                font = ImageFont.truetype(candidate, size=size)
                return font, f"System ({Path(candidate).stem})"
            except Exception:
                continue

    # 5. Fallback to Pillow built-in default font
    try:
        font = ImageFont.load_default(size=size)
        return font, "Pillow Default (Scaled)"
    except TypeError:
        font = ImageFont.load_default()
        return font, "Pillow Default"


def wrap_text_to_2_lines(
    text: str,
    font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
    max_width: int
) -> List[str]:
    """Wrap input text to at most 2 lines, truncating and adding ellipsis if needed."""
    if not text:
        return []

    normalized_text = str(text).replace("\\n", "\n").strip()
    if not normalized_text:
        return []

    explicit_lines = [p.strip() for p in normalized_text.split("\n") if p.strip()]

    def text_width(s: str) -> float:
        try:
            return font.getlength(s)
        except AttributeError:
            bbox = font.getbbox(s)
            return bbox[2] - bbox[0]

    words: List[str] = []
    for line in explicit_lines:
        words.extend(line.split())

    if not words:
        return []

    full_str = " ".join(words)
    if len(explicit_lines) <= 1 and text_width(full_str) <= max_width:
        return [full_str]

    line1_words: List[str] = []
    word_idx = 0
    first_explicit_words = explicit_lines[0].split() if explicit_lines else []

    while word_idx < len(words):
        candidate = " ".join(line1_words + [words[word_idx]])
        if text_width(candidate) <= max_width:
            line1_words.append(words[word_idx])
            word_idx += 1
            if len(explicit_lines) > 1 and word_idx == len(first_explicit_words):
                break
        else:
            if not line1_words:
                w = words[word_idx]
                trimmed = ""
                for char in w:
                    if text_width(trimmed + char) <= max_width:
                        trimmed += char
                    else:
                        break
                line1_words.append(trimmed)
                word_idx += 1
            break

    line1 = " ".join(line1_words)
    remaining_words = words[word_idx:]
    if not remaining_words:
        return [line1]

    line2_words: List[str] = []
    has_overflow = False

    while word_idx < len(words):
        candidate = " ".join(line2_words + [words[word_idx]])
        if text_width(candidate) <= max_width:
            line2_words.append(words[word_idx])
            word_idx += 1
        else:
            has_overflow = True
            break

    if word_idx < len(words) or has_overflow:
        ellipsis = "..."
        line2_candidate = " ".join(line2_words) if line2_words else remaining_words[0]
        truncated = line2_candidate
        while truncated and text_width(truncated + ellipsis) > max_width:
            truncated = truncated[:-1].rstrip()

        line2 = (truncated + ellipsis) if truncated else ellipsis
    else:
        line2 = " ".join(line2_words)

    return [line1, line2] if line2 else [line1]


def measure_text_lines(
    lines: List[str],
    font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
    line_height_multiplier: float = 1.1,
    line_spacing: int = 0
) -> Tuple[int, int, List[Tuple[int, int]]]:
    """Measure total dimensions and individual line sizes for wrapped lines."""
    if not lines:
        return 0, 0, []

    line_sizes = []
    max_w = 0

    sample_bbox = font.getbbox("AyHg")
    base_line_h = sample_bbox[3] - sample_bbox[1]
    line_step = int(round(base_line_h * line_height_multiplier)) + line_spacing

    for line in lines:
        try:
            w = int(round(font.getlength(line)))
        except AttributeError:
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
        line_sizes.append((w, base_line_h))
        if w > max_w:
            max_w = w

    if len(lines) == 1:
        total_h = base_line_h
    else:
        total_h = base_line_h + (len(lines) - 1) * line_step

    return max_w, total_h, line_sizes


def render_text_block(
    canvas: Image.Image,
    lines: List[str],
    font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
    text_color: RGBAColor,
    center_x: int,
    top_y: int,
    line_height_multiplier: float = 1.1,
    line_spacing: int = 0,
    text_bg: Optional[RGBAColor] = None,
    align: str = "center",
    margin_x: int = 40
) -> None:
    """Render wrapped text lines onto canvas with optional background pill and alignment."""
    if not lines:
        return

    draw = ImageDraw.Draw(canvas)
    total_w, total_h, line_sizes = measure_text_lines(
        lines,
        font,
        line_height_multiplier,
        line_spacing=line_spacing
    )

    sample_bbox = font.getbbox("AyHg")
    base_line_h = sample_bbox[3] - sample_bbox[1]
    line_step = int(round(base_line_h * line_height_multiplier)) + line_spacing

    if text_bg and text_bg[3] > 0:
        pad_x = 24
        pad_y = 12
        pill_left = center_x - (total_w // 2) - pad_x
        pill_top = top_y - pad_y
        pill_right = center_x + (total_w // 2) + pad_x
        pill_bottom = top_y + total_h + pad_y
        pill_radius = min(16, (pill_bottom - pill_top) // 2)

        pill_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        pill_draw = ImageDraw.Draw(pill_layer)
        pill_draw.rounded_rectangle(
            [pill_left, pill_top, pill_right, pill_bottom],
            radius=pill_radius,
            fill=text_bg
        )
        canvas.alpha_composite(pill_layer)
        draw = ImageDraw.Draw(canvas)

    current_y = top_y
    for i, line in enumerate(lines):
        line_w = line_sizes[i][0]
        if align == "left":
            line_x = margin_x
        elif align == "right":
            line_x = canvas.width - margin_x - line_w
        else:  # center
            line_x = center_x - (line_w // 2)

        draw.text((line_x, current_y), line, fill=text_color, font=font)
        current_y += line_step
