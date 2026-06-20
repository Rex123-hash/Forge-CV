"""Generate the full favicon set from static/img/logo.svg.

Tries cairosvg first; if cairo system libraries are unavailable (typical on
Windows), falls back to a pure-Pillow renderer that redraws the known logo
geometry at the requested pixel size.
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG = os.path.join(HERE, "static", "img", "logo.svg")
OUT = os.path.join(HERE, "static")
PNG_SIZES = {
    "favicon-16x16.png": 16, "favicon-32x32.png": 32,
    "apple-touch-icon.png": 180,
    "android-chrome-192x192.png": 192, "android-chrome-512x512.png": 512,
}

CORAL = (227, 93, 79, 255)
PALE  = (253, 238, 236, 255)
TRANSPARENT = (0, 0, 0, 0)

# SVG viewport is 64×64; all coords below are in that space.
_SVG_SIZE = 64


def _draw_logo_at(size: int) -> Image.Image:
    """Render the ForgeCV logo at *size*×*size* pixels via Pillow."""
    # Work at 4× for anti-aliasing then downscale.
    scale = 4
    w = h = size * scale
    s = scale * size / _SVG_SIZE   # pixels-per-SVG-unit

    img = Image.new("RGBA", (w, h), TRANSPARENT)
    d = ImageDraw.Draw(img)

    # Rounded-rect document body: x=14 y=8 w=30 h=44 rx=9
    rx, ry, rw, rh, corner = 14*s, 8*s, 30*s, 44*s, 9*s
    d.rounded_rectangle(
        [rx, ry, rx + rw, ry + rh],
        radius=corner,
        fill=PALE,
        outline=CORAL,
        width=round(3 * s),
    )

    # "Forge spark" lightning bolt: M40 24 L52 24 L33 56 L37 36 L26 36 Z
    bolt = [
        (40*s, 24*s),
        (52*s, 24*s),
        (33*s, 56*s),
        (37*s, 36*s),
        (26*s, 36*s),
    ]
    d.polygon(bolt, fill=CORAL)

    # Line 1: x1=20 y1=20 x2=32 y2=20
    lw = round(3 * s)
    d.line([(20*s, 20*s), (32*s, 20*s)], fill=CORAL, width=lw)
    # Line 2: x1=20 y1=28 x2=28 y2=28
    d.line([(20*s, 28*s), (28*s, 28*s)], fill=CORAL, width=lw)

    del d
    return img.resize((size, size), Image.LANCZOS)


def _render_cairosvg(svg_path, png_path, size):
    import cairosvg
    cairosvg.svg2png(url=svg_path, write_to=png_path,
                     output_width=size, output_height=size)


RENDERER_USED = "pillow-fallback"


def _render(svg_path, png_path, size):
    global RENDERER_USED
    try:
        _render_cairosvg(svg_path, png_path, size)
        RENDERER_USED = "cairosvg"
        return
    except Exception:
        pass
    img = _draw_logo_at(size)
    img.save(png_path, "PNG")
    RENDERER_USED = "pillow-fallback"


def main():
    for fname, size in PNG_SIZES.items():
        _render(SVG, os.path.join(OUT, fname), size)
    tmp = os.path.join(OUT, "_tmp.png")
    _render(SVG, tmp, 64)
    Image.open(tmp).convert("RGBA").save(
        os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    os.remove(tmp)
    print(f"Favicons generated. Renderer used: {RENDERER_USED}")


if __name__ == "__main__":
    main()
