
# Store Listing Screenshot CLI — Requirements & AI Prompt

## Summary
Create a command-line program that reads phone screenshots from an input folder and produces Play Store / App Store listing-ready images in an output folder. The program must be configurable via command-line flags to control padding, border radius, shadow, background gradient, text overlay (max 2 lines), and output dimensions. Default output size targets a standard phone screenshot for Google Play (1080×1920) but must be overridable.

---

## High-level goals
- Process up to N images from `input/` (1.png … 10.png) and write the processed outputs to `output/` using the exact same file names.
- Apply configurable paddings around the screenshot inside the canvas (left, right, top, bottom).
- Apply configurable rounded corners and optional border around the screenshot.
- Apply configurable shadow (color, blur radius, offset X/Y, opacity).
- Place screenshot on a configurable background which is a two-color gradient (horizontal or vertical).
- Add optional centered text (max 2 lines) anchored at the top or bottom of the canvas with center alignment and configurable font/size/color/line-height. If text exceeds two lines it should wrap and then truncate with ellipsis on the second line.
- Apply a global canvas border (independent widths/colors for top/right/bottom/left) optionally.
- Keep processing deterministic and produce images with the same file names as input.

---

## CLI design (required flags)
Name: `storeshot` (example)

Usage:
```
storeshot --input input --output output [flags]
```

Flags:
- `--input` (string, required) — input folder path (default: `input`).
- `--output` (string, required) — output folder path (default: `output`).
- `--pattern` (string) — glob pattern for input files (default: `*.png`).
- `--max-files` (int) — maximum files to process (default: 10).
- `--out-width` (int) — output canvas width in px (default: 1080).
- `--out-height` (int) — output canvas height in px (default: 1920).
- `--pad-left` / `--pad-right` / `--pad-top` / `--pad-bottom` (int px) — screenshot inner paddings (default: 40,40,120,200) — values relative to out-size; validate non-negative.
- `--screenshot-border-radius` (int px) — radius for screenshot corners (default: 32).
- `--screenshot-border-width` (int px) — width of screenshot stroke/border (default: 0).
- `--screenshot-border-color` (hex) — color for screenshot border (default: `#00000000` transparent).
- `--shadow-color` (hex) — shadow color, can include alpha (default: `#00000040`).
- `--shadow-blur` (int px) — blur radius for shadow (default: 40).
- `--shadow-offset-x` / `--shadow-offset-y` (int px) — shadow offset in px (default: 0, 24).
- `--bg-color-1` / `--bg-color-2` (hex) — two colors for gradient (required).
- `--bg-orientation` (`horizontal`|`vertical`) — (default: `vertical`).
- `--canvas-border-widths` (CSV of 4 ints) — e.g. `--canvas-border-widths 2,2,2,2` (top,right,bottom,left) (default: `0,0,0,0`).
- `--canvas-border-colors` (CSV of 4 hex colors) — colors for each side (default: all transparent).
- `--text` (string) — single text string; up to 2 lines allowed; newline may be provided via `\n` or programmatic wrap.
- `--text-position` (`top`|`bottom`) — where text appears (default: `bottom`).
- `--text-font` (path or font name) — fallback to system sans-serif if missing.
- `--text-size` (int or pct) — font size in px or percent of canvas height (default: 0.035 of height).
- `--text-color` (hex) — default `#FFFFFF`.
- `--text-line-height` (float) — multiplier (default: 1.1).
- `--text-padding` (int px) — distance between text block and the screenshot or canvas edge (default: 24).
- `--text-bg` (hex or `none`) — optional background (pill) behind text for contrast (default: `none`).
- `--dpi` (int) — output resolution DPI (default: 72).
- `--format` (`png`|`jpg`) — output format (default: `png`).
- `--quality` (int 1-100) — output jpeg quality if format=jpg (default: 90).
- `--overwrite` (bool) — overwrite existing outputs (default: false).
- `--workers` (int) — concurrent workers (default: 4).
- `--verbose` (bool) — verbose logging.
- `--dry-run` (bool) — validate and print actions but do not write outputs.

Validation rules:
- `pad-left + pad-right < out-width` and `pad-top + pad-bottom < out-height`.
- Colors validated as hex or rgba format.
- Font path validated if provided; fallback to bundled default.

---

## Processing steps (algorithm)
For each input image (in filename order):
1. Create canvas of size `out-width × out-height`.
2. Paint the background with a two-color gradient oriented as `bg-orientation` between `bg-color-1` and `bg-color-2`.
3. If `canvas-border-widths` > 0, draw borders on the canvas per side with the specified colors.
4. Compute inner rectangle for screenshot placement: `x = pad-left`, `y = pad-top`, `w = out-width - pad-left - pad-right`, `h = out-height - pad-top - pad-bottom`.
5. Load the input image, scale it down (preserving aspect ratio) to fit inside `(w, h)` using a `fit = contain` policy. Optionally `cover` if requested by flag.
6. If screenshot-border-radius > 0: apply rounded corner mask to the scaled image.
7. If screenshot-border-width > 0: render stroke around the screenshot (respecting rounded corners).
8. Render a shadow using parameters (blur, color, offset) behind the screenshot. Shadow must respect rounded corner silhouette.
9. Place the screenshot (with shadow) centered within the inner rectangle.
10. Render text block (if provided):
   - Wrap the text to at most 2 lines using given `text-size` and `text-line-height`. If text needs >2 lines, truncate the second line and append ellipsis.
   - Calculate the text block width = min(inner width, out-width * 0.9) minus `text-padding` margins.
   - Position the text block centered horizontally; vertically place it `text-padding` from top of canvas if `text-position=top`, or `text-padding` from bottom if `bottom`.
   - If `text-bg` provided, draw a rounded rectangle behind the text block sized to fit plus small padding.
11. Export the canvas to `output/<same filename>` with requested format and quality.

---

## Default values (recommended)
- `out-width=1080`, `out-height=1920` (Google Play phone default — override allowed)
- `pad-left/right=40`, `pad-top=120`, `pad-bottom=200`
- `screenshot-border-radius=32`
- `shadow-blur=40`, `shadow-offset-y=24`, `shadow-color=#00000040`
- `bg-color-1=#0f1724`, `bg-color-2=#0b1220`, `bg-orientation=vertical`
- `text-color=#FFFFFF`, `text-size=0.035*height`, `text-padding=24`

---

## Example CLI invocations
```bash
# simple run using defaults, write up to 10 images from ./input to ./output
storeshot --input ./input --output ./output --bg-color-1 "#0f1724" --bg-color-2 "#0b1220"

# specify top text, horizontal gradient, and custom paddings
storeshot --input ./input --output ./output --text "Simple UI with a light theme" --text-position top --bg-orientation horizontal --pad-left 60 --pad-right 60 --pad-top 140 --pad-bottom 120

# change output resolution (e.g., 1242×2688 for certain tall phone screenshots)
storeshot --input ./input --output ./output --out-width 1242 --out-height 2688
```

---

## Example ImageMagick composition (concept, not full code)
- Create the gradient base (background).
- Composite a blurred/offset rounded-corner shadow layer.
- Composite the rounded screenshot image above the shadow.
- Draw stroke/border around screenshot.
- Draw text block and optional text background.
- Export as PNG/JPEG.

(The exact ImageMagick one-liner will be long; prefer a small script that builds the composition step-by-step.)

---

## Example Python/Pillow flow (sketch, not implementation)
- Use Pillow to create RGBA canvas and gradient background.
- Use `ImageOps.fit` to resize screenshot to fit inner rect.
- Create mask image with rounded rectangle to apply corner radius.
- Create shadow by drawing mask onto a blurred layer, offset, and tinting.
- Paste shadow, then screenshot (using mask), then draw stroke by expanding masked region.
- Use `ImageDraw` + `ImageFont` to draw wrapped text and optional background pill.
- Save with requested format/quality.

---

## Logging, errors, and acceptance criteria
- For each input file, log: filename, input size, scaled size, output size, operations applied (radius, shadow, text).
- Exit code 0 on full success; >0 if errors occurred (list failed files).
- Acceptance test: provide 3 sample inputs and verify outputs match expected visuals and dimensions. The produced files must have identical names and be viewable in Play Console upload flow.

---

## Edge cases & notes
- If an input image DPI is not 72 and user requests different DPI, respect the requested DPI when saving metadata but do not resample unless `--resample` requested.
- If text font is missing, fall back to system sans-serif and note fallback in logs.
- If output format=jpg and transparency used (e.g., shadows), flatten over the gradient background before writing.
- If computed inner space is smaller than 200px in height or width, warn and skip unless `--force` provided.
- Provide a `--template` mode to export a JSON file capturing the effective computed layout for a single sample input (useful for design verification).

---

## AI prompt for generating the implementation
Use the following prompt with a code-generation model (e.g., GPT / Copilot / other). The prompt is explicit about features, CLI flags, and behavior; ask the model to produce a ready-to-run repository with tests and a README.


**AI prompt (paste to the code model):**

```
You are a developer. Create a command-line application named "storeshot" that produces store-listing screenshots from raw phone screenshots. Implementation language: choose one of: Python (preferred) using Pillow + Click/argparse, or an ImageMagick-based shell program. Include a full README, install instructions, and example inputs and outputs. Required features (implement exactly):

- Command-line flags as listed in the "CLI design" section of the attached spec. Provide defaults matching the spec.
- Input/Output handling: read `input/1.png...` up to `--max-files` and write to `output/` using the same filename.
- Canvas background: two-color gradient (horizontal or vertical).
- Inner paddings: left/right/top/bottom applied to computed inner rectangle where screenshot is placed.
- Scaling: preserve aspect ratio; `contain` by default; provide optional `--fit cover`.
- Rounded corner mask for screenshot and optional stroked border respecting radius.
- Shadow behind screenshot: color, blur, offset, opacity.
- Text overlay: optional, centered, max 2 lines; wrap/truncate with ellipsis on second line; support `--text-position` top/bottom; support optional text background pill.
- Canvas border: independent side widths and colors.
- Output size & format: default 1080×1920 PNG, overridable.
- Concurrency with `--workers` and progress/logging with `--verbose`.
- A `--dry-run` mode.
- Unit tests that verify: canvas size, paddings, rounded mask applied, and text rendering truncated to 2 lines.
- Provide 3 sample input images and example outputs in the repo, plus a minimal CI job that runs the tests.

Also include a short `USAGE.md` with examples of common command invocations and an `ACCEPTANCE.md` describing how to validate outputs in the Play Console. Keep the implementation clear, modular, and well-documented. Prioritize correctness for pixel placement and text truncation behavior. Do not include any unrelated features.
```

---

## Delivery
- This document is the single source of truth for the CLI requirements and the AI prompt for generating the implementation. Implementers should follow the spec verbatim for tests and flags.
- If you want, I can now generate an initial Python skeleton (CLI + placeholder functions + README) from this spec. Say "Generate skeleton" to proceed.
