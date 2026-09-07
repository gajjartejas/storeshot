"""Gradient image generation module."""

from __future__ import annotations

from typing import Tuple
from PIL import Image

RGBAColor = Tuple[int, int, int, int]


def create_gradient_image(
    width: int,
    height: int,
    color1: RGBAColor,
    color2: RGBAColor,
    orientation: str = "vertical"
) -> Image.Image:
    """Create a 2-color linear gradient image in RGBA mode."""
    if width <= 0 or height <= 0:
        raise ValueError(f"Dimensions must be positive, got {width}x{height}")

    r1, g1, b1, a1 = color1
    r2, g2, b2, a2 = color2

    if orientation == "vertical":
        if height == 1:
            strip = Image.new("RGBA", (1, 1), color1)
        else:
            strip_bytes = bytearray()
            for y in range(height):
                t = y / (height - 1)
                r = int(round(r1 + (r2 - r1) * t))
                g = int(round(g1 + (g2 - g1) * t))
                b = int(round(b1 + (b2 - b1) * t))
                a = int(round(a1 + (a2 - a1) * t))
                strip_bytes.extend((r, g, b, a))
            strip = Image.frombytes("RGBA", (1, height), bytes(strip_bytes))
        return strip.resize((width, height), Image.Resampling.NEAREST)

    elif orientation == "horizontal":
        if width == 1:
            strip = Image.new("RGBA", (1, 1), color1)
        else:
            strip_bytes = bytearray()
            for x in range(width):
                t = x / (width - 1)
                r = int(round(r1 + (r2 - r1) * t))
                g = int(round(g1 + (g2 - g1) * t))
                b = int(round(b1 + (b2 - b1) * t))
                a = int(round(a1 + (a2 - a1) * t))
                strip_bytes.extend((r, g, b, a))
            strip = Image.frombytes("RGBA", (width, 1), bytes(strip_bytes))
        return strip.resize((width, height), Image.Resampling.NEAREST)

    else:
        raise ValueError(
            f"Invalid orientation '{orientation}'. Expected 'vertical' or 'horizontal'."
        )
