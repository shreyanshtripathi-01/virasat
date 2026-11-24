"""Generate the Virasat app icons with Pillow only.

Run from the project root:
    .venv/bin/python scripts/make_icons.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "static" / "img" / "icons"
FONT_PATH = Path("/usr/share/fonts/gsfonts/NimbusRoman-Bold.otf")
TERRACOTTA = "#B5482A"
CREAM = "#FBF5E9"
TURMERIC = "#E3A018"


def _font(size):
    """Load the serif face used for the brand letter."""
    try:
        return ImageFont.truetype(str(FONT_PATH), size)
    except OSError:
        return ImageFont.truetype("DejaVuSerif-Bold.ttf", size)


def make_icon(size, maskable=False):
    """Return one square icon with a cream serif V on a terracotta ground."""
    scale = 4
    side = size * scale
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if maskable:
        draw.rectangle((0, 0, side, side), fill=TERRACOTTA)
    else:
        inset = round(side * 0.02)
        draw.rounded_rectangle(
            (inset, inset, side - inset, side - inset),
            radius=round(side * 0.22),
            fill=TERRACOTTA,
        )
    border = max(2, round(side * 0.012))
    margin = round(side * 0.09)
    draw.rounded_rectangle(
        (margin, margin, side - margin, side - margin),
        radius=round(side * 0.16),
        outline=TURMERIC,
        width=border,
    )
    letter_size = round(side * (0.42 if maskable else 0.52))
    font = _font(letter_size)
    box = draw.textbbox((0, 0), "V", font=font)
    width = box[2] - box[0]
    height = box[3] - box[1]
    position = ((side - width) / 2 - box[0], (side - height) / 2 - box[1] - round(side * 0.02))
    draw.text(position, "V", font=font, fill=CREAM)
    line_width = round(side * 0.14)
    line_y = round(side * 0.76)
    draw.rounded_rectangle(
        ((side - line_width) / 2, line_y, (side + line_width) / 2, line_y + border * 2),
        radius=border,
        fill=TURMERIC,
    )
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    return image.convert("RGB")


def main():
    """Write the four PNG files used by the manifest and Apple touch icon."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-512-maskable.png", 512, True),
        ("apple-touch-icon-180.png", 180, False),
    ]
    for name, size, maskable in targets:
        path = OUT_DIR / name
        make_icon(size, maskable=maskable).save(path, "PNG", optimize=True)
        print(f"wrote {path.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
