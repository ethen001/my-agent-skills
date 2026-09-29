#!/usr/bin/env python3
"""Extract exact colors from a design image so the YAML spec uses measured hex
values instead of eyeballed ones.

Usage:
  python extract_palette.py mockup.png                 # top colors for whole image
  python extract_palette.py mockup.png --top 12        # more swatches
  python extract_palette.py mockup.png --region 0,0,1440,72      # x,y,w,h  (e.g. the navbar)
  python extract_palette.py mockup.png --point 120,40             # single pixel (e.g. a logo)
  python extract_palette.py mockup.png --grid 4x6                 # dominant color per cell

Output is plain text you can paste into the `tokens.colors` section.
Requires Pillow (pip install pillow).
"""
import argparse
import sys
from collections import Counter

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install pillow --break-system-packages")


def to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb[:3])


def _pixels(img):
    # Pillow >= 11 prefers get_flattened_data; fall back quietly on older versions.
    if hasattr(img, "get_flattened_data"):
        return img.get_flattened_data()
    return img.getdata()


def dominant_colors(img, top=8, step=4):
    """Return [(hex, percent)] for the most common colors.

    Pixels are grouped on a coarse grid (``step`` levels per channel) so
    anti-aliasing noise collapses into its parent color, but the reported hex is
    the *exact* most frequent pixel inside each group — so a #2563EB button comes
    back as #2563EB, not as the center of a bucket.
    """
    small = img.convert("RGB")
    if small.width * small.height > 600_000:
        ratio = (600_000 / (small.width * small.height)) ** 0.5
        small = small.resize((max(1, int(small.width * ratio)), max(1, int(small.height * ratio))), Image.NEAREST)
    groups = Counter()
    exact = {}
    for px in _pixels(small):
        key = tuple(c // step for c in px)
        groups[key] += 1
        exact.setdefault(key, Counter())[px] += 1
    total = sum(groups.values())
    out = []
    for key, n in groups.most_common(top):
        best = exact[key].most_common(1)[0][0]
        out.append((to_hex(best), round(100 * n / total, 1)))
    return out


def luminance(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--region", help="x,y,w,h crop to analyze")
    ap.add_argument("--point", help="x,y single pixel sample")
    ap.add_argument("--grid", help="ROWSxCOLS dominant color per cell, e.g. 4x6")
    ap.add_argument("--contrast", nargs=2, metavar=("FG", "BG"), help="WCAG contrast ratio of two hex colors")
    args = ap.parse_args()

    if args.contrast:
        fg, bg = args.contrast
        ratio = contrast(fg, bg)
        verdict = "AAA" if ratio >= 7 else "AA" if ratio >= 4.5 else "AA-large only" if ratio >= 3 else "FAIL"
        print(f"contrast {fg} on {bg}: {ratio}:1  ({verdict})")
        return

    img = Image.open(args.image).convert("RGB")
    print(f"image: {args.image}  size: {img.width}x{img.height}")

    if args.point:
        x, y = map(int, args.point.split(","))
        print(f"point ({x},{y}): {to_hex(img.getpixel((x, y)))}")
        return

    if args.region:
        x, y, w, h = map(int, args.region.split(","))
        img = img.crop((x, y, x + w, y + h))
        print(f"region: x={x} y={y} w={w} h={h}")

    if args.grid:
        rows, cols = map(int, args.grid.lower().split("x"))
        cw, ch = img.width / cols, img.height / rows
        print(f"grid {rows}x{cols} (dominant color per cell, row-major):")
        for r in range(rows):
            cells = []
            for c in range(cols):
                cell = img.crop((int(c * cw), int(r * ch), int((c + 1) * cw), int((r + 1) * ch)))
                cells.append(dominant_colors(cell, top=1)[0][0])
            print(f"  row {r}: " + "  ".join(cells))
        return

    print("dominant colors (hex, % coverage):")
    for hx, pct in dominant_colors(img, top=args.top):
        print(f"  {hx}  {pct:>5}%")


if __name__ == "__main__":
    main()
