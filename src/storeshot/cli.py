"""Command line interface for StoreShot."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from .config import THEMES, StoreShotConfig, load_json_config
from .core import process_batch


def setup_logging(verbose: bool) -> None:
    """Configure logging format and verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(level=level, format=format_str, datefmt="%H:%M:%S", force=True)


@click.command(
    name="storeshot",
    help="Produce Play Store / App Store listing-ready graphics from screenshots."
)
@click.option(
    "--config", "-c", "config_file", default=None, type=click.Path(path_type=Path),
    help="Path to JSON configuration file containing root and per-screenshot configs."
)
@click.option(
    "--input", "-i", "input_dir", default="input", show_default=True,
    type=click.Path(path_type=Path), help="Input folder path containing screenshots."
)
@click.option(
    "--output", "-o", "output_dir", default="output", show_default=True,
    type=click.Path(path_type=Path), help="Output folder path for generated graphics."
)
@click.option(
    "--pattern", default="*.png", show_default=True,
    help="Glob pattern to find input files."
)
@click.option(
    "--max-files", default=10, show_default=True, type=int,
    help="Maximum number of files to process."
)
@click.option(
    "--out-width", default=1080, show_default=True, type=int,
    help="Output canvas width in px."
)
@click.option(
    "--out-height", default=1920, show_default=True, type=int,
    help="Output canvas height in px."
)
@click.option(
    "--pad-left", default=40, show_default=True, type=int,
    help="Screenshot left inner padding in px."
)
@click.option(
    "--pad-right", default=40, show_default=True, type=int,
    help="Screenshot right inner padding in px."
)
@click.option(
    "--pad-top", default=120, show_default=True, type=int,
    help="Screenshot top inner padding in px."
)
@click.option(
    "--pad-bottom", default=200, show_default=True, type=int,
    help="Screenshot bottom inner padding in px."
)
@click.option(
    "--screenshot-border-radius", default=32, show_default=True, type=int,
    help="Radius for screenshot rounded corners in px."
)
@click.option(
    "--screenshot-border-width", default=0, show_default=True, type=int,
    help="Stroke width around screenshot in px."
)
@click.option(
    "--screenshot-border-color", default="#00000000", show_default=True,
    help="Color for screenshot border stroke."
)
@click.option(
    "--shadow-color", default="#00000040", show_default=True,
    help="Drop shadow color with alpha."
)
@click.option(
    "--shadow-blur", default=40, show_default=True, type=int,
    help="Blur radius for shadow in px."
)
@click.option(
    "--shadow-offset-x", default=0, show_default=True, type=int,
    help="Shadow horizontal offset in px."
)
@click.option(
    "--shadow-offset-y", default=24, show_default=True, type=int,
    help="Shadow vertical offset in px."
)
@click.option(
    "--bg-color-1", default="#0f1724", show_default=True,
    help="Start color for background gradient."
)
@click.option(
    "--bg-color-2", default="#0b1220", show_default=True,
    help="End color for background gradient."
)
@click.option(
    "--bg-orientation", type=click.Choice(["vertical", "horizontal"], case_sensitive=False),
    default="vertical", show_default=True, help="Gradient orientation."
)
@click.option(
    "--canvas-border-widths", default="0,0,0,0", show_default=True,
    help="CSV widths (top,right,bottom,left) for canvas borders."
)
@click.option(
    "--canvas-border-colors", default="#00000000,#00000000,#00000000,#00000000",
    show_default=True, help="CSV hex colors for canvas borders."
)
@click.option(
    "--text", default=None,
    help="Text string overlay (up to 2 lines, wraps/truncates)."
)
@click.option(
    "--text-position", type=click.Choice(["top", "bottom"], case_sensitive=False),
    default="bottom", show_default=True, help="Vertical anchor position for text."
)
@click.option(
    "--text-font", default=None,
    help="Font file path or system font name."
)
@click.option(
    "--text-font-weight", default="normal", show_default=True,
    help="Font weight variant (normal, bold, semibold)."
)
@click.option(
    "--text-size", default=None, type=float,
    help="Font size in px or percentage (e.g. 0.035) of canvas height."
)
@click.option(
    "--text-color", default="#FFFFFF", show_default=True,
    help="Hex or RGBA color for text."
)
@click.option(
    "--text-line-height", default=1.1, show_default=True, type=float,
    help="Line height multiplier."
)
@click.option(
    "--text-line-spacing", default=0, show_default=True, type=int,
    help="Explicit vertical line spacing in px."
)
@click.option(
    "--text-padding", default=24, show_default=True, type=int,
    help="Distance between text block and canvas edge."
)
@click.option(
    "--text-bg", default="none", show_default=True,
    help="Optional background pill color behind text."
)
@click.option(
    "--dpi", default=72, show_default=True, type=int,
    help="Output image DPI metadata."
)
@click.option(
    "--format", "fmt", type=click.Choice(["png", "jpg", "jpeg"], case_sensitive=False),
    default="png", show_default=True, help="Output image format."
)
@click.option(
    "--quality", default=90, show_default=True, type=int,
    help="Output quality if format=jpg (1-100)."
)
@click.option(
    "--fit", type=click.Choice(["contain", "cover"], case_sensitive=False),
    default="contain", show_default=True,
    help="Image fit mode inside inner rectangle."
)
@click.option(
    "--overwrite", is_flag=True, default=False,
    help="Overwrite existing output files."
)
@click.option(
    "--workers", default=4, show_default=True, type=int,
    help="Number of concurrent worker threads."
)
@click.option(
    "--verbose", "-v", is_flag=True, default=False,
    help="Enable verbose debug logging."
)
@click.option(
    "--dry-run", is_flag=True, default=False,
    help="Validate and plan operations without writing files."
)
@click.option(
    "--theme", type=click.Choice(list(THEMES.keys()), case_sensitive=False),
    default=None, help="Apply a preset theme token set (e.g., antigravity)."
)
@click.option(
    "--resample", is_flag=True, default=False,
    help="Resample image when DPI differs."
)
@click.option(
    "--force", is_flag=True, default=False,
    help="Force processing even if inner rectangle is smaller than 200px."
)
@click.option(
    "--template", default=None,
    help="Export computed layout for first processed image as JSON."
)
@click.pass_context
def main(
    ctx: click.Context,
    config_file: Optional[Path],
    input_dir: Path,
    output_dir: Path,
    pattern: str,
    max_files: int,
    out_width: int,
    out_height: int,
    pad_left: int,
    pad_right: int,
    pad_top: int,
    pad_bottom: int,
    screenshot_border_radius: int,
    screenshot_border_width: int,
    screenshot_border_color: str,
    shadow_color: str,
    shadow_blur: int,
    shadow_offset_x: int,
    shadow_offset_y: int,
    bg_color_1: str,
    bg_color_2: str,
    bg_orientation: str,
    canvas_border_widths: str,
    canvas_border_colors: str,
    text: Optional[str],
    text_position: str,
    text_font: Optional[str],
    text_font_weight: str,
    text_size: Optional[float],
    text_color: str,
    text_line_height: float,
    text_line_spacing: int,
    text_padding: int,
    text_bg: str,
    dpi: int,
    fmt: str,
    quality: int,
    fit: str,
    overwrite: bool,
    workers: int,
    verbose: bool,
    dry_run: bool,
    theme: Optional[str],
    resample: bool,
    force: bool,
    template: Optional[str]
) -> None:
    """StoreShot CLI entrypoint."""
    setup_logging(verbose)
    logger = logging.getLogger("storeshot")

    child_items = None

    if config_file and Path(config_file).is_dir():
        # Directory mode: discover all JSON configurations in the directory tree
        candidate_configs = sorted([
            p for p in Path(config_file).rglob("*.json")
            if p.name not in ("package.json", "tsconfig.json", "template.json")
        ])
        if not candidate_configs:
            logger.error(f"No JSON configuration files found in '{config_file}'")
            sys.exit(1)

        logger.info(
            f"Found {len(candidate_configs)} project config(s) in '{config_file}'"
        )
        grand_successful = 0
        grand_failed = 0

        for cfg_file in candidate_configs:
            proj_name = (
                cfg_file.parent.name
                if cfg_file.parent.name != "input"
                else cfg_file.parent.parent.name
            )
            rel_cfg = cfg_file.relative_to(config_file)
            logger.info(f"=== Project: {proj_name} ({rel_cfg}) ===")
            try:
                proj_cfg, proj_items = load_json_config(cfg_file)
                if overwrite:
                    proj_cfg.overwrite = True
                if dry_run:
                    proj_cfg.dry_run = True
                if verbose:
                    proj_cfg.verbose = True
                proj_cfg.validate()
                succ, fail = process_batch(proj_cfg, items=proj_items)
                grand_successful += len(succ)
                grand_failed += len(fail)
            except Exception as e:
                logger.error(f"Failed project '{cfg_file}': {e}")
                grand_failed += 1

        logger.info(
            f"All projects complete: {grand_successful} generated, "
            f"{grand_failed} failed across {len(candidate_configs)} project(s)."
        )
        sys.exit(1 if grand_failed > 0 else 0)

    if config_file:
        try:
            config, child_items = load_json_config(config_file)
            logger.info(
                f"Loaded configuration from '{config_file}' with "
                f"{len(child_items)} item configs"
            )
        except Exception as e:
            logger.error(f"Failed to load configuration file '{config_file}': {e}")
            sys.exit(2)
    else:
        config = StoreShotConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            pattern=pattern,
            max_files=max_files,
            out_width=out_width,
            out_height=out_height,
            pad_left=pad_left,
            pad_right=pad_right,
            pad_top=pad_top,
            pad_bottom=pad_bottom,
            screenshot_border_radius=screenshot_border_radius,
            screenshot_border_width=screenshot_border_width,
            screenshot_border_color=screenshot_border_color,
            shadow_color=shadow_color,
            shadow_blur=shadow_blur,
            shadow_offset_x=shadow_offset_x,
            shadow_offset_y=shadow_offset_y,
            bg_color_1=bg_color_1,
            bg_color_2=bg_color_2,
            bg_orientation=bg_orientation,
            canvas_border_widths=canvas_border_widths,
            canvas_border_colors=canvas_border_colors,
            text=text,
            text_position=text_position,
            text_font=text_font,
            text_font_weight=text_font_weight,
            text_size=text_size,
            text_color=text_color,
            text_line_height=text_line_height,
            text_line_spacing=text_line_spacing,
            text_padding=text_padding,
            text_bg=text_bg,
            dpi=dpi,
            format=fmt,
            quality=quality,
            fit=fit,
            overwrite=overwrite,
            workers=workers,
            verbose=verbose,
            dry_run=dry_run,
            theme=theme,
            resample=resample,
            force=force,
            template=template
        )

        if theme:
            config.apply_theme(theme)

    # Re-apply any parameters explicitly passed via command line
    for param_name, param_val in ctx.params.items():
        if param_name in ("config_file", "theme"):
            continue
        if ctx.get_parameter_source(param_name) == click.core.ParameterSource.COMMANDLINE:
            if param_name == "fmt":
                config.format = param_val
            else:
                setattr(config, param_name, param_val)

    if ctx.get_parameter_source("theme") == click.core.ParameterSource.COMMANDLINE and theme:
        config.apply_theme(theme)

    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(2)

    logger.info(
        f"Starting StoreShot batch: input='{config.input_dir}', output='{config.output_dir}', "
        f"size={config.out_width}x{config.out_height}, theme={config.theme or 'default'}, "
        f"dry_run={config.dry_run}"
    )

    try:
        successful, failed = process_batch(config, items=child_items)
    except Exception as e:
        logger.error(f"Execution error: {e}")
        sys.exit(1)

    logger.info(
        f"Finished processing: {len(successful)} succeeded, {len(failed)} failed."
    )

    if failed:
        logger.error("The following files failed to process:")
        for failed_path, err_msg in failed:
            logger.error(f"  - {failed_path.name}: {err_msg}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
