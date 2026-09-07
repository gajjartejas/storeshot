"""Drop shadow generation for rounded screenshots."""

from __future__ import annotations

from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter

RGBAColor = Tuple[int, int, int, int]


def create_drop_shadow(
    width: int,
    height: int,
    border_radius: int,
    shadow_blur: int,
    shadow_color: RGBAColor,
    offset_x: int = 0,
    offset_y: int = 24
) -> Tuple[Optional[Image.Image], int, int]:
    """Generate a drop shadow image matching the rounded silhouette of a screenshot."""
    sr, sg, sb, sa = shadow_color
    if sa <= 0 or width <= 0 or height <= 0:
        return None, 0, 0

    effective_radius = min(border_radius, width // 2, height // 2)
    blur_margin = max(int(shadow_blur * 3), 10) if shadow_blur > 0 else 0
    shadow_canvas_w = width + 2 * blur_margin
    shadow_canvas_h = height + 2 * blur_margin

    mask = Image.new("L", (shadow_canvas_w, shadow_canvas_h), 0)
    draw = ImageDraw.Draw(mask)

    box = (blur_margin, blur_margin, blur_margin + width, blur_margin + height)
    if effective_radius > 0:
        draw.rounded_rectangle(box, radius=effective_radius, fill=255)
    else:
        draw.rectangle(box, fill=255)

    if shadow_blur > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=shadow_blur))

    if sa < 255:
        alpha_table = [int(round(i * (sa / 255.0))) for i in range(256)]
        mask = mask.point(alpha_table)

    shadow_img = Image.new("RGBA", (shadow_canvas_w, shadow_canvas_h), (sr, sg, sb, 0))
    shadow_img.putalpha(mask)

    relative_x = offset_x - blur_margin
    relative_y = offset_y - blur_margin

    return shadow_img, relative_x, relative_y
