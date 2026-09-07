# StoreShot — Usage Guide & Examples

This document demonstrates common command invocations for creating app store listing screenshots using `storeshot`.

---

## Example 1: JSON Configuration File with Root Defaults & Child Overrides (Recommended)

Execute a complete store screenshot batch configured via `input.json` where each screenshot has custom text and styling while inheriting global defaults:

```bash
storeshot --config examples/input.json --overwrite
```

---

## Example 2: Antigravity Theme with Bottom Headline via CLI

Apply the **Antigravity** theme preset (deep midnight indigo palette, neon iris rim, elevated shadow, and frosted pill) with centered headline text:

```bash
storeshot \
  --input ./examples/input \
  --output ./examples/output \
  --theme antigravity \
  --text "Real-Time Insights\nMonitor metrics and scale effortlessly" \
  --text-position bottom \
  --overwrite
```

---

## Example 3: Top Text Overlay with Horizontal Gradient & Custom Paddings

Anchor the text headline at the top with a horizontal vibrant gradient, customized paddings, and background pill:

```bash
storeshot \
  --input ./input \
  --output ./output \
  --bg-color-1 "#1e3a8a" \
  --bg-color-2 "#0f172a" \
  --bg-orientation horizontal \
  --pad-left 60 \
  --pad-right 60 \
  --pad-top 160 \
  --pad-bottom 120 \
  --text "Seamless Collaboration\nConnect with your team instantly" \
  --text-position top \
  --text-bg "#00000080" \
  --text-color "#F1F5F9" \
  --overwrite
```

---

## Example 4: Apple App Store 6.7" Super Retina (1290×2796)

Produce high-resolution assets formatted for iPhone 15 Pro Max / 16 Pro Max display dimensions with custom stroked borders:

```bash
storeshot \
  --input ./input \
  --output ./output_ios \
  --out-width 1290 \
  --out-height 2796 \
  --pad-left 50 \
  --pad-right 50 \
  --pad-top 160 \
  --pad-bottom 260 \
  --screenshot-border-radius 48 \
  --screenshot-border-width 4 \
  --screenshot-border-color "#38BDF8" \
  --shadow-color "#00000080" \
  --shadow-blur 60 \
  --shadow-offset-y 36 \
  --text "Pro Level Security\nEncrypted data at rest and in transit" \
  --text-position bottom \
  --overwrite
```

---

## Example 5: High-Quality JPEG Export with Cover Fit & Layout Template

Generate JPEG listing assets with `cover` scaling policy, 95% JPEG quality, 8 parallel worker threads, and export computed layout metadata as a JSON template:

```bash
storeshot \
  --input ./input \
  --output ./output_jpg \
  --format jpg \
  --quality 95 \
  --fit cover \
  --workers 8 \
  --theme antigravity \
  --text "Lightning Fast Sync\nInstant updates across all devices" \
  --template ./output_jpg/layout_template.json \
  --overwrite \
  --verbose
```
