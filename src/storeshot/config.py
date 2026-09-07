"""Configuration models, theme definitions, and validation logic for StoreShot."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

RGBAColor = Tuple[int, int, int, int]


def normalize_config_key(key: str) -> str:
    """Normalize configuration key from kebab-case or camelCase to snake_case."""
    # Convert kebab-case to snake_case
    s = key.replace("-", "_")
    # Convert camelCase to snake_case
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = re.sub(r"([a-zA-Z])([0-9])", r"\1_\2", s)
    return s.lower()


def parse_color(val: Optional[str]) -> RGBAColor:
    """Parse color string (hex #RGB, #RGBA, #RRGGBB, #RRGGBBAA, rgb/rgba, none) to RGBA tuple."""
    if val is None:
        return (0, 0, 0, 0)

    val_clean = str(val).strip().lower()
    if val_clean in ("none", "transparent", ""):
        return (0, 0, 0, 0)

    # Hex formats
    if val_clean.startswith("#"):
        hex_str = val_clean[1:]
        if len(hex_str) == 3:  # #RGB
            r = int(hex_str[0] * 2, 16)
            g = int(hex_str[1] * 2, 16)
            b = int(hex_str[2] * 2, 16)
            return (r, g, b, 255)
        elif len(hex_str) == 4:  # #RGBA
            r = int(hex_str[0] * 2, 16)
            g = int(hex_str[1] * 2, 16)
            b = int(hex_str[2] * 2, 16)
            a = int(hex_str[3] * 2, 16)
            return (r, g, b, a)
        elif len(hex_str) == 6:  # #RRGGBB
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return (r, g, b, 255)
        elif len(hex_str) == 8:  # #RRGGBBAA
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            a = int(hex_str[6:8], 16)
            return (r, g, b, a)
        else:
            raise ValueError(
                f"Invalid hex color format: '{val}'. Expected #RGB, #RGBA, #RRGGBB, or #RRGGBBAA."
            )

    # rgba(r, g, b, a) or rgb(r, g, b)
    pattern = (
        r"^rgba?\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?:\s*,\s*([\d.]+))?\s*\)$"
    )
    rgb_match = re.match(pattern, val_clean)
    if rgb_match:
        r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
        a_str = rgb_match.group(4)
        if a_str is not None:
            a_val = float(a_str)
            a = int(round(a_val * 255)) if a_val <= 1.0 else int(round(a_val))
        else:
            a = 255
        for c in (r, g, b, a):
            if not (0 <= c <= 255):
                raise ValueError(f"RGB values must be between 0 and 255 in '{val}'")
        return (r, g, b, a)

    raise ValueError(f"Unsupported color format: '{val}'")


def parse_csv_ints(val: str, expected_count: int = 4) -> Tuple[int, ...]:
    """Parse comma-separated integers."""
    parts = [p.strip() for p in str(val).split(",") if p.strip()]
    if len(parts) != expected_count:
        raise ValueError(
            f"Expected {expected_count} comma-separated integers, got {len(parts)} in '{val}'"
        )
    try:
        return tuple(int(p) for p in parts)
    except ValueError as e:
        raise ValueError(f"Invalid integer in CSV '{val}': {e}") from e


def parse_csv_colors(val: str, expected_count: int = 4) -> Tuple[RGBAColor, ...]:
    """Parse comma-separated color strings."""
    parts = [p.strip() for p in str(val).split(",") if p.strip()]
    if len(parts) != expected_count:
        raise ValueError(
            f"Expected {expected_count} comma-separated colors, got {len(parts)} in '{val}'"
        )
    return tuple(parse_color(p) for p in parts)


# Antigravity Theme and Default Theme Tokens
THEMES = {
    "default": {
        "bg_color_1": "#0f1724",
        "bg_color_2": "#0b1220",
        "bg_orientation": "vertical",
        "screenshot_border_radius": 32,
        "screenshot_border_width": 0,
        "screenshot_border_color": "#00000000",
        "shadow_color": "#00000040",
        "shadow_blur": 40,
        "shadow_offset_x": 0,
        "shadow_offset_y": 24,
        "text_color": "#FFFFFF",
        "text_bg": "none",
    },
    "antigravity": {
        "bg_color_1": "#1E1B4B",           # Deep indigo space
        "bg_color_2": "#0F172A",           # Slate abyss
        "bg_orientation": "vertical",
        "screenshot_border_radius": 36,
        "screenshot_border_width": 3,
        "screenshot_border_color": "#818CF8",  # Vibrant neon iris rim
        "shadow_color": "#00000099",       # Rich deep elevation shadow
        "shadow_blur": 48,
        "shadow_offset_x": 0,
        "shadow_offset_y": 28,
        "text_color": "#F8FAFC",
        "text_bg": "none",
    }
}


@dataclass
class StoreShotConfig:
    """Configuration options for screenshot generation."""

    input_dir: Path = field(default_factory=lambda: Path("input"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    pattern: str = "*.png"
    max_files: int = 10

    # Canvas dimensions
    out_width: int = 1080
    out_height: int = 1920

    # Paddings
    pad_left: int = 40
    pad_right: int = 40
    pad_top: int = 120
    pad_bottom: int = 200

    # Screenshot styling
    screenshot_border_radius: int = 32
    screenshot_border_width: int = 0
    screenshot_border_color: str = "#00000000"

    # Shadow styling
    shadow_color: str = "#00000040"
    shadow_blur: int = 40
    shadow_offset_x: int = 0
    shadow_offset_y: int = 24

    # Background gradient
    bg_color_1: str = "#0f1724"
    bg_color_2: str = "#0b1220"
    bg_orientation: str = "vertical"  # 'vertical' or 'horizontal'

    # Canvas border
    canvas_border_widths: str = "0,0,0,0"  # top, right, bottom, left
    canvas_border_colors: str = "#00000000,#00000000,#00000000,#00000000"

    # Text overlay
    text: Optional[str] = None
    text_position: str = "bottom"  # 'top' or 'bottom'
    text_font: Optional[str] = None
    text_font_weight: str = "normal"  # 'normal', 'bold', 'semibold'
    text_align: str = "center"  # 'center', 'left', 'right'
    text_size: Optional[Union[int, float]] = None  # None -> 0.035 * height
    text_color: str = "#FFFFFF"
    text_line_height: float = 1.1
    text_line_spacing: int = 0
    text_padding: int = 24
    text_margin_top: Optional[int] = None
    text_margin_bottom: Optional[int] = None
    text_bg: str = "none"

    # Export options
    dpi: int = 72
    format: str = "png"  # 'png' or 'jpg'
    quality: int = 90
    fit: str = "contain"  # 'contain' or 'cover'
    overwrite: bool = False
    workers: int = 4
    verbose: bool = False
    dry_run: bool = False
    theme: Optional[str] = None
    resample: bool = False
    force: bool = False
    template: Optional[str] = None

    def apply_theme(self, theme_name: str) -> None:
        """Apply a predefined theme token set to this configuration."""
        theme_name_clean = theme_name.strip().lower()
        if theme_name_clean not in THEMES:
            raise ValueError(
                f"Unknown theme '{theme_name}'. Available themes: {list(THEMES.keys())}"
            )

        tokens = THEMES[theme_name_clean]
        for key, val in tokens.items():
            setattr(self, key, val)
        self.theme = theme_name_clean

    def apply_dict(self, data: Dict[str, Any]) -> None:
        """Apply a dictionary of options to this config with key normalization and aliases."""
        # Check if theme is specified first
        theme_val = None
        for raw_k, v in data.items():
            k = normalize_config_key(raw_k)
            if k == "theme" and v:
                theme_val = str(v)
                break

        if theme_val:
            self.apply_theme(theme_val)

        alias_map = {
            "font": "text_font",
            "font_family": "text_font",
            "font_name": "text_font",
            "font_weight": "text_font_weight",
            "weight": "text_font_weight",
            "font_size": "text_size",
            "size": "text_size",
            "font_color": "text_color",
            "color": "text_color",
            "font_padding": "text_padding",
            "line_height": "text_line_height",
            "line_spacing": "text_line_spacing",
            "text_spacing": "text_line_spacing",
            "text_spacing_y": "text_line_spacing",
            "vertical_spacing": "text_line_spacing",
            "align": "text_align",
            "position": "text_position",
            "text_margin_top": "text_margin_top",
            "text_top": "text_margin_top",
            "text_pad_top": "text_margin_top",
            "font_margin_top": "text_margin_top",
            "text_top_margin": "text_margin_top",
            "text_margin_bottom": "text_margin_bottom",
            "text_bottom": "text_margin_bottom",
            "text_pad_bottom": "text_margin_bottom",
            "font_margin_bottom": "text_margin_bottom",
            "text_bottom_margin": "text_margin_bottom",
        }

        for raw_k, v in data.items():
            k = normalize_config_key(raw_k)
            if k in ("theme", "screenshots", "items", "images", "inputs"):
                continue

            target_attr = alias_map.get(k, k)
            if hasattr(self, target_attr):
                if target_attr in ("input_dir", "output_dir"):
                    setattr(self, target_attr, Path(v))
                else:
                    setattr(self, target_attr, v)

    def merge_child(self, child_data: Dict[str, Any]) -> StoreShotConfig:
        """Create a new StoreShotConfig inheriting root settings and applying child overrides."""
        child_cfg = copy.deepcopy(self)
        child_cfg.apply_dict(child_data)
        return child_cfg

    def validate(self) -> None:
        """Validate configuration rules per specification."""
        if self.out_width <= 0 or self.out_height <= 0:
            raise ValueError(
                f"Output dimensions must be positive, got {self.out_width}x{self.out_height}"
            )

        if self.pad_left + self.pad_right >= self.out_width:
            raise ValueError(
                f"pad-left ({self.pad_left}) + pad-right ({self.pad_right}) "
                f"must be less than out-width ({self.out_width})"
            )

        if self.pad_top + self.pad_bottom >= self.out_height:
            raise ValueError(
                f"pad-top ({self.pad_top}) + pad-bottom ({self.pad_bottom}) "
                f"must be less than out-height ({self.out_height})"
            )

        inner_w = self.out_width - self.pad_left - self.pad_right
        inner_h = self.out_height - self.pad_top - self.pad_bottom
        if (inner_w < 200 or inner_h < 200) and not self.force:
            raise ValueError(
                f"Computed inner screenshot area ({inner_w}x{inner_h}) is smaller than 200px. "
                "Adjust paddings/dimensions or pass --force to proceed."
            )

        if self.bg_orientation not in ("horizontal", "vertical"):
            raise ValueError(
                f"bg-orientation must be 'horizontal' or 'vertical', got '{self.bg_orientation}'"
            )

        if self.text_position not in ("top", "bottom"):
            raise ValueError(
                f"text-position must be 'top' or 'bottom', got '{self.text_position}'"
            )

        if self.fit not in ("contain", "cover"):
            raise ValueError(f"fit mode must be 'contain' or 'cover', got '{self.fit}'")

        if self.format.lower() not in ("png", "jpg", "jpeg"):
            raise ValueError(f"format must be 'png' or 'jpg', got '{self.format}'")

        if not (1 <= self.quality <= 100):
            raise ValueError(f"quality must be between 1 and 100, got {self.quality}")

        if self.dpi <= 0:
            raise ValueError(f"DPI must be positive, got {self.dpi}")

        if self.workers <= 0:
            raise ValueError(f"workers must be at least 1, got {self.workers}")

        # Validate colors
        parse_color(self.bg_color_1)
        parse_color(self.bg_color_2)
        parse_color(self.screenshot_border_color)
        parse_color(self.shadow_color)
        parse_color(self.text_color)
        if self.text_bg and self.text_bg.lower() != "none":
            parse_color(self.text_bg)

        # Validate CSV properties
        parse_csv_ints(self.canvas_border_widths, 4)
        parse_csv_colors(self.canvas_border_colors, 4)


def load_json_config(
    json_path: Union[str, Path],
    base_config: Optional[StoreShotConfig] = None
) -> Tuple[StoreShotConfig, List[Dict[str, Any]]]:
    """Load JSON config file containing root configuration and child screenshot configs.

    Returns:
        (root_config, child_items_list)
    """
    path = Path(json_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: '{path}'")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    root_cfg = copy.deepcopy(base_config) if base_config else StoreShotConfig()

    if isinstance(data, list):
        # The file is directly a list of screenshot configs
        if not base_config:
            root_cfg.input_dir = path.parent
        return root_cfg, data
    elif isinstance(data, dict):
        # Extract child array from common keys: screenshots, items, inputs, images
        child_items = None
        for array_key in ("screenshots", "items", "inputs", "images", "screens"):
            if array_key in data and isinstance(data[array_key], list):
                child_items = data[array_key]
                break

        # Apply root-level configuration
        root_cfg.apply_dict(data)

        # If input_dir was not explicitly passed in dict, default to JSON file's folder
        norm_keys = [normalize_config_key(k) for k in data.keys()]
        if "input_dir" not in norm_keys and "input" not in norm_keys:
            root_cfg.input_dir = path.parent
        elif not root_cfg.input_dir.is_absolute():
            root_cfg.input_dir = (path.parent / root_cfg.input_dir).resolve()

        if "output_dir" in norm_keys or "output" in norm_keys:
            if not root_cfg.output_dir.is_absolute():
                root_cfg.output_dir = (path.parent / root_cfg.output_dir).resolve()

        if child_items is None:
            child_items = []

        return root_cfg, child_items
    else:
        raise ValueError(
            f"Invalid JSON configuration structure in '{path}'. Expected dict or list."
        )
