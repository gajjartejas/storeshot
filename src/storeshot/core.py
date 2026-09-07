"""Core processing pipeline for StoreShot."""

from __future__ import annotations

import concurrent.futures
import json
import logging
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from .config import (
    RGBAColor,
    StoreShotConfig,
    parse_color,
    parse_csv_colors,
    parse_csv_ints,
)
from .gradient import create_gradient_image
from .shadow import create_drop_shadow
from .typography import (
    measure_text_lines,
    render_text_block,
    resolve_font,
    wrap_text_to_2_lines,
)

logger = logging.getLogger("storeshot")


def natural_sort_key(s: str) -> List[Any]:
    """Key for natural sorting of filenames (e.g., '1.png', '2.png', '10.png')."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", str(s))
    ]


def draw_canvas_borders(
    canvas: Image.Image,
    widths: Tuple[int, int, int, int],
    colors: Tuple[RGBAColor, RGBAColor, RGBAColor, RGBAColor]
) -> None:
    """Draw inset borders on the canvas (top, right, bottom, left)."""
    top_w, right_w, bottom_w, left_w = widths
    top_col, right_col, bottom_col, left_col = colors
    w, h = canvas.size

    border_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_layer)

    if top_w > 0 and top_col[3] > 0:
        draw.rectangle([0, 0, w, top_w], fill=top_col)

    if right_w > 0 and right_col[3] > 0:
        draw.rectangle([w - right_w, 0, w, h], fill=right_col)

    if bottom_w > 0 and bottom_col[3] > 0:
        draw.rectangle([0, h - bottom_w, w, h], fill=bottom_col)

    if left_w > 0 and left_col[3] > 0:
        draw.rectangle([0, 0, left_w, h], fill=left_col)

    canvas.alpha_composite(border_layer)


def create_rounded_mask(width: int, height: int, radius: int) -> Image.Image:
    """Create an antialiased 8-bit grayscale mask with rounded corners."""
    effective_radius = min(radius, width // 2, height // 2)
    if effective_radius <= 0:
        return Image.new("L", (width, height), 255)

    scale = 4
    super_w = width * scale
    super_h = height * scale
    super_r = effective_radius * scale

    super_mask = Image.new("L", (super_w, super_h), 0)
    draw = ImageDraw.Draw(super_mask)
    draw.rounded_rectangle([0, 0, super_w, super_h], radius=super_r, fill=255)

    return super_mask.resize((width, height), Image.Resampling.LANCZOS)


def draw_stroked_rim(
    canvas: Image.Image,
    box: Tuple[int, int, int, int],
    radius: int,
    stroke_width: int,
    stroke_color: RGBAColor
) -> None:
    """Draw a stroked rounded border on the canvas."""
    if stroke_width <= 0 or stroke_color[3] <= 0:
        return

    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0
    effective_radius = min(radius, w // 2, h // 2)

    scale = 4
    layer_w = (w + stroke_width * 2) * scale
    layer_h = (h + stroke_width * 2) * scale
    super_radius = effective_radius * scale
    super_stroke = stroke_width * scale

    stroke_img = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(stroke_img)

    offset = stroke_width * scale
    draw.rounded_rectangle(
        [offset, offset, offset + w * scale, offset + h * scale],
        radius=super_radius,
        outline=stroke_color,
        width=super_stroke
    )

    downscaled = stroke_img.resize(
        (w + stroke_width * 2, h + stroke_width * 2),
        Image.Resampling.LANCZOS
    )
    canvas.paste(
        downscaled,
        (x0 - stroke_width, y0 - stroke_width),
        mask=downscaled
    )


def process_single_image(
    input_path: Path,
    output_path: Path,
    config: StoreShotConfig
) -> Dict[str, Any]:
    """Process a single screenshot image and export the finished store graphic."""
    config.validate()

    c1 = parse_color(config.bg_color_1)
    c2 = parse_color(config.bg_color_2)
    canvas = create_gradient_image(
        config.out_width,
        config.out_height,
        c1,
        c2,
        orientation=config.bg_orientation
    )

    border_widths = parse_csv_ints(config.canvas_border_widths, 4)
    border_colors = parse_csv_colors(config.canvas_border_colors, 4)
    draw_canvas_borders(canvas, border_widths, border_colors)

    inner_x = config.pad_left
    inner_y = config.pad_top
    inner_w = config.out_width - config.pad_left - config.pad_right
    inner_h = config.out_height - config.pad_top - config.pad_bottom

    with Image.open(input_path) as raw_img:
        orig_w, orig_h = raw_img.size
        img = raw_img.convert("RGBA")

    if config.fit == "cover":
        scale = max(inner_w / orig_w, inner_h / orig_h)
        scaled_w = int(round(orig_w * scale))
        scaled_h = int(round(orig_h * scale))
        resized = img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

        crop_x = (scaled_w - inner_w) // 2
        crop_y = (scaled_h - inner_h) // 2
        scaled_img = resized.crop((crop_x, crop_y, crop_x + inner_w, crop_y + inner_h))
        final_w, final_h = inner_w, inner_h
    else:
        scale = min(inner_w / orig_w, inner_h / orig_h)
        final_w = int(round(orig_w * scale))
        final_h = int(round(orig_h * scale))
        scaled_img = img.resize((final_w, final_h), Image.Resampling.LANCZOS)

    operations_applied = []
    if config.screenshot_border_radius > 0:
        mask = create_rounded_mask(final_w, final_h, config.screenshot_border_radius)
        current_alpha = scaled_img.split()[3]
        combined_alpha = Image.composite(
            current_alpha,
            Image.new("L", (final_w, final_h), 0),
            mask
        )
        scaled_img.putalpha(combined_alpha)
        operations_applied.append(f"radius={config.screenshot_border_radius}px")

    screenshot_x = inner_x + (inner_w - final_w) // 2
    screenshot_y = inner_y + (inner_h - final_h) // 2

    shadow_color = parse_color(config.shadow_color)
    if shadow_color[3] > 0:
        shadow_img, rel_x, rel_y = create_drop_shadow(
            width=final_w,
            height=final_h,
            border_radius=config.screenshot_border_radius,
            shadow_blur=config.shadow_blur,
            shadow_color=shadow_color,
            offset_x=config.shadow_offset_x,
            offset_y=config.shadow_offset_y
        )
        if shadow_img is not None:
            canvas.paste(
                shadow_img,
                (screenshot_x + rel_x, screenshot_y + rel_y),
                mask=shadow_img
            )
            ops_desc = (
                f"shadow(blur={config.shadow_blur}, "
                f"offset={config.shadow_offset_x},{config.shadow_offset_y})"
            )
            operations_applied.append(ops_desc)

    canvas.paste(scaled_img, (screenshot_x, screenshot_y), mask=scaled_img)

    stroke_color = parse_color(config.screenshot_border_color)
    if config.screenshot_border_width > 0 and stroke_color[3] > 0:
        draw_stroked_rim(
            canvas,
            (screenshot_x, screenshot_y, screenshot_x + final_w, screenshot_y + final_h),
            radius=config.screenshot_border_radius,
            stroke_width=config.screenshot_border_width,
            stroke_color=stroke_color
        )
        operations_applied.append(f"border_stroke={config.screenshot_border_width}px")

    text_info = None
    if config.text:
        if config.text_size is None:
            font_size = int(round(config.out_height * 0.035))
        elif isinstance(config.text_size, float) and config.text_size <= 1.0:
            font_size = int(round(config.out_height * config.text_size))
        else:
            font_size = int(round(config.text_size))

        font_size = max(font_size, 10)
        font, font_desc = resolve_font(
            config.text_font,
            size=font_size,
            weight=config.text_font_weight
        )

        max_text_w = max(
            int(config.out_width - 2 * config.text_padding),
            100
        )
        wrapped_lines = wrap_text_to_2_lines(config.text, font, max_text_w)

        if wrapped_lines:
            tot_w, tot_h, _ = measure_text_lines(
                wrapped_lines,
                font,
                config.text_line_height,
                line_spacing=config.text_line_spacing
            )
            center_x = config.out_width // 2

            if config.text_position == "top":
                top_y = (
                    config.text_margin_top
                    if config.text_margin_top is not None
                    else config.text_padding
                )
            else:
                margin_b = (
                    config.text_margin_bottom
                    if config.text_margin_bottom is not None
                    else config.text_padding
                )
                top_y = config.out_height - tot_h - margin_b

            text_color = parse_color(config.text_color)
            text_bg_color = (
                parse_color(config.text_bg)
                if config.text_bg and config.text_bg.lower() != "none"
                else None
            )

            render_text_block(
                canvas,
                lines=wrapped_lines,
                font=font,
                text_color=text_color,
                center_x=center_x,
                top_y=top_y,
                line_height_multiplier=config.text_line_height,
                line_spacing=config.text_line_spacing,
                text_bg=text_bg_color,
                align=config.text_align
            )
            operations_applied.append(
                f"text(lines={len(wrapped_lines)}, pos={config.text_position})"
            )
            text_info = {
                "lines": wrapped_lines,
                "position": config.text_position,
                "font": font_desc,
                "font_size": font_size,
                "bounds": [
                    center_x - tot_w // 2,
                    top_y,
                    center_x + tot_w // 2,
                    top_y + tot_h
                ]
            }

    fmt = config.format.lower()
    if fmt in ("jpg", "jpeg"):
        final_output = Image.new("RGB", canvas.size, (255, 255, 255))
        final_output.paste(canvas, mask=canvas.split()[3])
        save_kwargs: Dict[str, Any] = {"format": "JPEG", "quality": config.quality}
    else:
        final_output = canvas
        save_kwargs = {"format": "PNG"}

    if config.dpi:
        save_kwargs["dpi"] = (config.dpi, config.dpi)

    if not config.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_output.save(output_path, **save_kwargs)

    result_summary = {
        "filename": input_path.name,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "input_size": [orig_w, orig_h],
        "scaled_size": [final_w, final_h],
        "output_size": [config.out_width, config.out_height],
        "screenshot_placement": [
            screenshot_x,
            screenshot_y,
            screenshot_x + final_w,
            screenshot_y + final_h
        ],
        "operations": operations_applied,
        "text_info": text_info,
        "format": fmt.upper(),
        "dry_run": config.dry_run
    }
    return result_summary


def process_batch(
    config: StoreShotConfig,
    items: Optional[List[Dict[str, Any]]] = None
) -> Tuple[List[Dict[str, Any]], List[Tuple[Path, str]]]:
    """Process all matching images or configured JSON items.

    If items is provided, each item will inherit root config and apply its specific overrides.
    """
    config.validate()

    pending_tasks: List[Tuple[Path, Path, StoreShotConfig]] = []
    successful_results: List[Dict[str, Any]] = []
    failed_files: List[Tuple[Path, str]] = []

    if items:
        # Processing explicitly defined screenshot objects from JSON
        for item in items:
            item_cfg = config.merge_child(item)
            item_cfg.validate()

            file_key = (
                item.get("file")
                or item.get("input")
                or item.get("filename")
                or item.get("image")
                or item.get("name")
            )
            if not file_key:
                logger.error(f"Child config missing 'file' or 'input' identifier: {item}")
                continue

            in_path = Path(file_key)
            if not in_path.is_absolute():
                in_path = Path(item_cfg.input_dir) / in_path

            ext = ".jpg" if item_cfg.format.lower() in ("jpg", "jpeg") else ".png"
            out_key = item.get("output") or item.get("output_file")
            if out_key:
                out_path = Path(out_key)
                if not out_path.is_absolute():
                    out_path = Path(item_cfg.output_dir) / out_path
            else:
                out_path = Path(item_cfg.output_dir) / (in_path.stem + ext)

            if out_path.exists() and not item_cfg.overwrite and not item_cfg.dry_run:
                logger.info(
                    f"Skipping '{in_path.name}' (output exists, use --overwrite to replace)"
                )
                continue

            pending_tasks.append((in_path, out_path, item_cfg))

    else:
        # Standard directory discovery mode
        input_dir = Path(config.input_dir)
        output_dir = Path(config.output_dir)

        if not input_dir.exists() or not input_dir.is_dir():
            raise FileNotFoundError(f"Input directory does not exist: '{input_dir}'")

        all_files = sorted(
            [p for p in input_dir.glob(config.pattern) if p.is_file()],
            key=lambda p: natural_sort_key(p.name)
        )

        if not all_files:
            logger.warning(
                f"No files matching pattern '{config.pattern}' found in '{input_dir}'."
            )
            return [], []

        files_to_process = all_files[: config.max_files]
        ext = ".jpg" if config.format.lower() in ("jpg", "jpeg") else ".png"

        for in_file in files_to_process:
            out_filename = in_file.stem + ext
            out_file = output_dir / out_filename

            if out_file.exists() and not config.overwrite and not config.dry_run:
                logger.info(
                    f"Skipping '{in_file.name}' (output exists, use --overwrite to replace)"
                )
                continue

            pending_tasks.append((in_file, out_file, config))

    if not pending_tasks:
        return [], []

    max_workers = min(config.workers, len(pending_tasks))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_single_image, in_p, out_p, cfg): (in_p, out_p)
            for in_p, out_p, cfg in pending_tasks
        }

        for future in concurrent.futures.as_completed(future_to_file):
            in_p, out_p = future_to_file[future]
            try:
                res = future.result()
                successful_results.append(res)
                ops_str = ", ".join(res["operations"]) if res["operations"] else "none"
                logger.info(
                    f"Processed '{res['filename']}': "
                    f"in={res['input_size'][0]}x{res['input_size'][1]} -> "
                    f"scaled={res['scaled_size'][0]}x{res['scaled_size'][1]} -> "
                    f"out={res['output_size'][0]}x{res['output_size'][1]} | ops=[{ops_str}]"
                )
            except Exception as exc:
                logger.error(f"Failed to process '{in_p.name}': {exc}")
                failed_files.append((in_p, str(exc)))

    if config.template and successful_results:
        template_path = Path(config.template)
        template_data = {
            "config": {
                k: v for k, v in asdict(config).items() if not isinstance(v, Path)
            },
            "sample_layout": successful_results[0]
        }
        template_data["config"]["input_dir"] = str(config.input_dir)
        template_data["config"]["output_dir"] = str(config.output_dir)

        template_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(template_data, f, indent=2)
        logger.info(f"Exported layout template to '{template_path}'")

    return successful_results, failed_files
