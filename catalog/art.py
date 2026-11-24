"""Original, reproducible craft artwork generated with Pillow only.

No downloaded images are used. Each product gets a seeded pattern by craft and a
product silhouette by item type. The same product slug always produces the same
image, while different slugs produce different composition and colour choices.
"""

import math
import random
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

CANVAS = (1200, 1500)
COVER_SIZE = (800, 800)
JPEG_LIMIT = 250 * 1024


# Palettes use a light base for the object, a darker ink and one accent family.
CRAFT_PALETTES = {
    "madhubani": [
        {
            "base": "#F2E0B8", "ink": "#2C241E", "red": "#A93B2F",
            "green": "#3E6B4A", "gold": "#C98A2E", "cream": "#FBF5E9",
            "backdrop": ("#F6EAD6", "#D9C39B"),
        },
        {
            "base": "#E8D1A6", "ink": "#253031", "red": "#8E2F2B",
            "green": "#486E4A", "gold": "#D2A03A", "cream": "#FDF8EC",
            "backdrop": ("#EEDCC1", "#C8AA79"),
        },
    ],
    "pattachitra": [
        {
            "base": "#EFE0BE", "ink": "#201A17", "red": "#A53B2D",
            "yellow": "#D8A62E", "gold": "#D8A62E", "cream": "#FBF5E9",
            "backdrop": ("#F4E8D0", "#D5BC91"),
        },
        {
            "base": "#E7D0A3", "ink": "#2A2018", "red": "#8A2E28",
            "yellow": "#E0B43D", "gold": "#E0B43D", "cream": "#FDF8EC",
            "backdrop": ("#EAD4AE", "#C7A66F"),
        },
    ],
    "bagru-block-print": [
        {
            "base": "#F4EBDD", "indigo": "#243F68", "ochre": "#C58B2E",
            "madder": "#9B3B2D", "pale": "#E7C79A", "gold": "#C58B2E", "cream": "#FBF5E9",
            "ink": "#2A2520", "backdrop": ("#F8F0E4", "#D7C3A4"),
        },
        {
            "base": "#EFE3D0", "indigo": "#1E3656", "ochre": "#D09B39",
            "madder": "#A44432", "pale": "#EBD2A8", "gold": "#D09B39", "cream": "#FDF8EC",
            "ink": "#2A2520", "backdrop": ("#F1E4D1", "#CBB18B"),
        },
    ],
    "bandhani": [
        {
            "base": "#721D2A", "deep": "#4E1420", "yellow": "#E9B84A",
            "white": "#F8EED7", "pink": "#D68086", "gold": "#E9B84A", "cream": "#F8EED7",
            "ink": "#3A111A", "backdrop": ("#EFE3D2", "#BFA281"),
        },
        {
            "base": "#5A1B28", "deep": "#3C101A", "yellow": "#F0C257",
            "white": "#FBF2DE", "pink": "#C96F79", "gold": "#F0C257", "cream": "#FBF2DE",
            "ink": "#3A111A", "backdrop": ("#E9DDCB", "#B89A78"),
        },
        {
            "base": "#8B2533", "deep": "#5F1722", "yellow": "#F2C052",
            "white": "#FCF4E1", "pink": "#E09AA0", "gold": "#F2C052", "cream": "#FCF4E1",
            "ink": "#3A111A", "backdrop": ("#F2E6D4", "#C6A986"),
        },
    ],
    "phulkari": [
        {
            "base": "#7B2433", "deep": "#571722", "yellow": "#F0B646",
            "orange": "#E06A31", "cream": "#F4E1B6", "pink": "#CE5F8A",
            "green": "#2F6A58", "gold": "#F0B646", "ink": "#4A1A22",
            "backdrop": ("#EFE2CC", "#B99C75"),
        },
        {
            "base": "#244B3B", "deep": "#173327", "yellow": "#F2BD4C",
            "orange": "#D9622D", "cream": "#F6E6C0", "pink": "#D26A88",
            "green": "#477D5C", "gold": "#F2BD4C", "ink": "#1D2A22",
            "backdrop": ("#E9DCC7", "#B39A76"),
        },
    ],
    "kantha": [
        {
            "base": "#F0E5D0", "cream": "#FBF5E9", "indigo": "#2B4868",
            "red": "#A84A3E", "yellow": "#D9AE49", "gold": "#D9AE49", "ink": "#3F3A32", "soft": "#E8C7A8",
            "backdrop": ("#F8F0E1", "#D5C2A5"),
        },
        {
            "base": "#EDE0CB", "cream": "#FDF7EA", "indigo": "#354F6D",
            "red": "#944237", "yellow": "#D9AC3B", "gold": "#D9AC3B", "ink": "#3F3A32", "soft": "#E6BEB2",
            "backdrop": ("#F5EBDC", "#CEB99B"),
        },
    ],
    "channapatna-toys": [
        {
            "base": "#C98A4A", "wood": "#9B6332", "red": "#C8442A",
            "yellow": "#F0B52A", "gold": "#F0B52A", "green": "#3E8B5A", "indigo": "#2A3B6B",
            "ink": "#4C2B18", "cream": "#FBF0D8",
            "backdrop": ("#F3E7D2", "#CDB28A"),
        },
        {
            "base": "#D09A55", "wood": "#A66B36", "red": "#B93B2B",
            "yellow": "#E9A929", "gold": "#E9A929", "green": "#2F7A50", "indigo": "#25345F",
            "ink": "#4C2B18", "cream": "#FCF2DE",
            "backdrop": ("#F1E2C9", "#C7A97B"),
        },
    ],
    "dhokra": [
        {
            "base": "#24251E", "deep": "#151611", "brass": "#B98A3F",
            "gold": "#D8B56A", "patina": "#5C7A58", "cream": "#EADFC3",
            "ink": "#141510", "backdrop": ("#332F27", "#171814"),
        },
        {
            "base": "#2C2A21", "deep": "#181813", "brass": "#C3984C",
            "gold": "#E1C077", "patina": "#6B8660", "cream": "#F0E5C9",
            "ink": "#141510", "backdrop": ("#3A352B", "#1B1C17"),
        },
    ],
    "blue-pottery": [
        {
            "base": "#F4F0E5", "cobalt": "#204A96", "turquoise": "#2D96A1",
            "pale": "#A9D6DF", "yellow": "#D8B24C", "gold": "#D8B24C", "ink": "#203C63", "cream": "#FCF8EE",
            "backdrop": ("#F7F1E4", "#C9D7D1"),
        },
        {
            "base": "#F0EBDD", "cobalt": "#173D82", "turquoise": "#23838E",
            "pale": "#B7DEE3", "yellow": "#D6A83C", "gold": "#D6A83C", "ink": "#203C63", "cream": "#FDFAF2",
            "backdrop": ("#F0E9DA", "#BCCFCC"),
        },
    ],
}

CRAFT_RENDERERS = {}


def _rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _rgba(value, alpha=255):
    return _rgb(value) + (alpha,)


def _inset(box, margin):
    x1, y1, x2, y2 = box
    return (x1 + margin, y1 + margin, x2 - margin, y2 - margin)


def _vertical_gradient(size, top, bottom):
    width, height = size
    image = Image.new("RGBA", size)
    draw = ImageDraw.Draw(image)
    start = _rgb(top)
    end = _rgb(bottom)
    for y in range(height):
        ratio = y / max(1, height - 1)
        colour = tuple(round(start[i] + (end[i] - start[i]) * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=colour + (255,))
    return image


def _paper_backdrop(size, palette, rng):
    top, bottom = palette["backdrop"]
    image = _vertical_gradient(size, top, bottom)
    width, height = size
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        (width * 0.08, height * 0.04, width * 0.92, height * 0.78),
        fill=_rgba(palette.get("cream", "#FBF5E9"), 75),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(width * 0.12))
    image.alpha_composite(glow)

    noise_size = (max(40, width // 5), max(40, height // 5))
    noise_values = bytes(
        max(0, min(255, int(rng.gauss(128, 24))))
        for _ in range(noise_size[0] * noise_size[1])
    )
    noise = Image.frombytes("L", noise_size, noise_values)
    noise = noise.resize(size, Image.Resampling.BILINEAR)
    noise_layer = Image.merge(
        "RGBA",
        (noise, noise, noise, Image.new("L", size, 12)),
    )
    image.alpha_composite(noise_layer)

    shadow = Image.new("L", size, 0)
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(
        (width * 0.20, height * 0.82, width * 0.80, height * 0.96),
        fill=110,
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(width * 0.08))
    shadow_layer = Image.new("RGBA", size, (45, 30, 20, 255))
    shadow_layer.putalpha(shadow)
    image.alpha_composite(shadow_layer)
    return image


def _vignette(image):
    width, height = image.size
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (-width * 0.28, -height * 0.20, width * 1.28, height * 1.20),
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(width * 0.18))
    mask = mask.point(lambda value: int((255 - value) * 0.30))
    dark = Image.new("RGBA", image.size, (35, 22, 14, 255))
    dark.putalpha(mask)
    image.alpha_composite(dark)
    return image


def _flower(draw, cx, cy, radius, petal_colour, centre_colour, petals=8, petal_ratio=0.52):
    petal_radius = max(2, int(radius * petal_ratio))
    for index in range(petals):
        angle = (math.tau / petals) * index
        px = cx + math.cos(angle) * radius * 0.68
        py = cy + math.sin(angle) * radius * 0.68
        draw.ellipse(
            (px - petal_radius, py - petal_radius,
             px + petal_radius, py + petal_radius),
            fill=petal_colour,
        )
    centre_radius = max(2, int(radius * 0.30))
    draw.ellipse(
        (cx - centre_radius, cy - centre_radius,
         cx + centre_radius, cy + centre_radius),
        fill=centre_colour,
    )


def _lotus(draw, cx, cy, radius, colours):
    main, accent, centre = colours
    petals = [
        [(cx, cy - radius), (cx + radius * 0.30, cy - radius * 0.18),
         (cx, cy + radius * 0.34)],
        [(cx, cy - radius), (cx - radius * 0.30, cy - radius * 0.18),
         (cx, cy + radius * 0.34)],
        [(cx - radius * 0.82, cy - radius * 0.10),
         (cx - radius * 0.18, cy - radius * 0.40), (cx, cy + radius * 0.28)],
        [(cx + radius * 0.82, cy - radius * 0.10),
         (cx + radius * 0.18, cy - radius * 0.40), (cx, cy + radius * 0.28)],
        [(cx - radius * 0.62, cy + radius * 0.42),
         (cx - radius * 0.20, cy - radius * 0.04), (cx, cy + radius * 0.72)],
        [(cx + radius * 0.62, cy + radius * 0.42),
         (cx + radius * 0.20, cy - radius * 0.04), (cx, cy + radius * 0.72)],
    ]
    for points in petals:
        draw.polygon(points, fill=main, outline=accent)
    draw.ellipse(
        (cx - radius * 0.20, cy + radius * 0.16,
         cx + radius * 0.20, cy + radius * 0.56),
        fill=centre,
    )


def _fish(draw, cx, cy, width, height, body, outline, accent):
    body_points = [
        (cx - width * 0.50, cy), (cx - width * 0.30, cy - height * 0.42),
        (cx + width * 0.18, cy - height * 0.50), (cx + width * 0.46, cy),
        (cx + width * 0.18, cy + height * 0.50), (cx - width * 0.30, cy + height * 0.42),
    ]
    draw.polygon(body_points, fill=body, outline=outline)
    draw.polygon(
        [(cx + width * 0.40, cy), (cx + width * 0.70, cy - height * 0.34),
         (cx + width * 0.70, cy + height * 0.34)],
        fill=body, outline=outline,
    )
    eye_radius = max(2, int(width * 0.035))
    eye_x = cx - width * 0.28
    draw.ellipse(
        (eye_x - eye_radius, cy - eye_radius, eye_x + eye_radius, cy + eye_radius),
        fill=outline,
    )
    draw.arc(
        (cx - width * 0.18, cy - height * 0.20, cx + width * 0.10, cy + height * 0.20),
        120, 240, fill=accent, width=max(2, int(height * 0.06)),
    )


def _leaf(draw, cx, cy, width, height, colour, outline=None, angle=-0.5):
    direction = math.cos(angle)
    lean = math.sin(angle)
    points = [
        (cx, cy - height * 0.50),
        (cx + width * 0.42 * direction, cy - height * 0.08 + lean * width * 0.2),
        (cx, cy + height * 0.50),
        (cx - width * 0.42 * direction, cy - height * 0.08 - lean * width * 0.2),
    ]
    draw.polygon(points, fill=colour, outline=outline)
    draw.line((cx, cy - height * 0.42, cx, cy + height * 0.36), fill=outline, width=1)


def _buta(draw, cx, cy, width, height, colour, outline):
    draw.ellipse(
        (cx - width * 0.24, cy - height * 0.34,
         cx + width * 0.24, cy + height * 0.06),
        fill=colour, outline=outline,
    )
    draw.polygon(
        [(cx, cy + height * 0.42), (cx - width * 0.18, cy + height * 0.02),
         (cx + width * 0.18, cy + height * 0.02)],
        fill=colour, outline=outline,
    )
    draw.line((cx, cy + height * 0.30, cx, cy + height * 0.48), fill=outline, width=2)
    for side in (-1, 1):
        _leaf(
            draw, cx + side * width * 0.32, cy + height * 0.12,
            width * 0.26, height * 0.44, colour, outline, angle=side * 0.5,
        )
    draw.ellipse(
        (cx - width * 0.08, cy - height * 0.18,
         cx + width * 0.08, cy - height * 0.02),
        fill=outline,
    )


def _diamond(draw, cx, cy, radius, colours, width=3, stitches=False):
    for index, colour in enumerate(colours):
        size = radius * (1 - index * 0.20)
        draw.polygon(
            [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)],
            outline=colour, width=width,
        )
    if stitches:
        step = max(4, int(radius * 0.20))
        for offset in range(-radius + step, radius, step):
            draw.line(
                (cx + offset, cy - (radius - abs(offset)),
                 cx + offset, cy + (radius - abs(offset))),
                fill=colours[-1], width=2,
            )


def _sun(draw, cx, cy, radius, outer, inner, centre):
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=outer)
    draw.ellipse(
        (cx - radius * 0.72, cy - radius * 0.72,
         cx + radius * 0.72, cy + radius * 0.72),
        fill=inner,
    )
    draw.ellipse(
        (cx - radius * 0.34, cy - radius * 0.34,
         cx + radius * 0.34, cy + radius * 0.34),
        fill=centre,
    )
    for index in range(12):
        angle = math.tau * index / 12
        draw.line(
            (cx + math.cos(angle) * radius * 1.04, cy + math.sin(angle) * radius * 1.04,
             cx + math.cos(angle) * radius * 1.28, cy + math.sin(angle) * radius * 1.28),
            fill=outer, width=max(2, int(radius * 0.08)),
        )


def _spiral(draw, cx, cy, radius, colour, width=3, turns=3.0):
    points = []
    steps = 54
    for index in range(steps + 1):
        angle = turns * math.tau * index / steps
        current = radius * index / steps
        points.append(
            (cx + math.cos(angle) * current, cy + math.sin(angle) * current)
        )
    draw.line(points, fill=colour, width=width, joint="curve")


def _tribal_figure(draw, cx, cy, height, colour):
    head = height * 0.10
    draw.ellipse((cx - head, cy - height * 0.48, cx + head, cy - height * 0.28), fill=colour)
    draw.polygon(
        [(cx, cy - height * 0.28), (cx - height * 0.16, cy + height * 0.22),
         (cx + height * 0.16, cy + height * 0.22)],
        fill=colour,
    )
    draw.line(
        (cx - height * 0.16, cy - height * 0.12, cx - height * 0.38, cy + height * 0.18),
        fill=colour, width=max(2, int(height * 0.045)),
    )
    draw.line(
        (cx + height * 0.16, cy - height * 0.12, cx + height * 0.38, cy + height * 0.18),
        fill=colour, width=max(2, int(height * 0.045)),
    )
    draw.line(
        (cx - height * 0.07, cy + height * 0.20, cx - height * 0.18, cy + height * 0.48),
        fill=colour, width=max(2, int(height * 0.05)),
    )
    draw.line(
        (cx + height * 0.07, cy + height * 0.20, cx + height * 0.18, cy + height * 0.48),
        fill=colour, width=max(2, int(height * 0.05)),
    )
    draw.ellipse(
        (cx - height * 0.025, cy - height * 0.41,
         cx + height * 0.025, cy - height * 0.36),
        fill=(255, 255, 255, 210),
    )


def draw_madhubani(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    step = max(18, int(width / 26))
    for x in range(x1 + step, x2, step):
        draw.line((x, y1, x, y2), fill=_rgba(palette["gold"], 45), width=1)
    draw.rectangle(_inset(box, 16), outline=_rgba(palette["ink"]), width=7)
    draw.rectangle(_inset(box, 34), outline=_rgba(palette["red"]), width=4)
    for index in range(8):
        angle = math.tau * index / 8
        cx = (x1 + x2) / 2 + math.cos(angle) * width * 0.30
        cy = (y1 + y2) / 2 + math.sin(angle) * height * 0.30
        _lotus(
            draw, cx, cy, min(width, height) * 0.065,
            (_rgba(palette["red"]), _rgba(palette["ink"]), _rgba(palette["gold"])),
        )
    _sun(
        draw, (x1 + x2) / 2, (y1 + y2) / 2, min(width, height) * 0.20,
        _rgba(palette["ink"]), _rgba(palette["red"]), _rgba(palette["gold"]),
    )
    _flower(
        draw, (x1 + x2) / 2, (y1 + y2) / 2, min(width, height) * 0.10,
        _rgba(palette["green"]), _rgba(palette["cream"]), petals=9,
    )
    for _ in range(7):
        side = rng.choice([-1, 1])
        cx = (x1 + x2) / 2 + side * width * rng.uniform(0.24, 0.40)
        cy = (y1 + y2) / 2 + rng.uniform(-0.30, 0.30) * height
        _fish(
            draw, cx, cy, width * 0.20, height * 0.13,
            _rgba(palette["cream"]), _rgba(palette["ink"]), _rgba(palette["red"]),
        )
    for _ in range(20):
        cx = rng.uniform(x1 + 40, x2 - 40)
        cy = rng.uniform(y1 + 40, y2 - 40)
        radius = rng.uniform(3, 8)
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=_rgba(palette["green"]),
        )


CRAFT_RENDERERS["madhubani"] = draw_madhubani


def draw_pattachitra(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    draw.rectangle(_inset(box, 14), outline=_rgba(palette["red"]), width=9)
    draw.rectangle(_inset(box, 30), outline=_rgba(palette["ink"]), width=3)
    scallop = max(22, int(width / 20))
    for x in range(x1 + scallop, x2 - scallop, scallop * 2):
        draw.arc(
            (x - scallop, y1 + 18, x + scallop, y1 + 18 + scallop * 2),
            0, 180, fill=_rgba(palette["red"]), width=5,
        )
        draw.arc(
            (x - scallop, y2 - 18 - scallop * 2, x + scallop, y2 - 18),
            180, 360, fill=_rgba(palette["red"]), width=5,
        )
    for y in range(y1 + scallop * 2, y2 - scallop, scallop * 2):
        draw.arc(
            (x1 + 18, y - scallop, x1 + 18 + scallop * 2, y + scallop),
            90, 270, fill=_rgba(palette["red"]), width=5,
        )
        draw.arc(
            (x2 - 18 - scallop * 2, y - scallop, x2 - 18, y + scallop),
            270, 90, fill=_rgba(palette["red"]), width=5,
        )
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    radius = min(width, height) * 0.23
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=_rgba(palette["red"]), outline=_rgba(palette["ink"]), width=6,
    )
    draw.ellipse(
        (cx - radius * 0.78, cy - radius * 0.78,
         cx + radius * 0.78, cy + radius * 0.78),
        fill=_rgba(palette["yellow"]), outline=_rgba(palette["ink"]), width=3,
    )
    for index in range(12):
        angle = math.tau * index / 12
        _flower(
            draw,
            cx + math.cos(angle) * radius * 0.56,
            cy + math.sin(angle) * radius * 0.56,
            radius * 0.12, _rgba(palette["cream"]), _rgba(palette["red"]),
            petals=5,
        )
    _sun(
        draw, cx, cy, radius * 0.43,
        _rgba(palette["ink"]), _rgba(palette["red"]), _rgba(palette["yellow"]),
    )
    for side in (-1, 1):
        _flower(
            draw, cx + side * width * 0.28, cy + height * 0.34,
            min(width, height) * 0.06,
            _rgba(palette["red"]), _rgba(palette["cream"]), petals=7,
        )
    for _ in range(18):
        cx = rng.uniform(x1 + 55, x2 - 55)
        cy = rng.uniform(y1 + 55, y2 - 55)
        draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=_rgba(palette["yellow"]))


CRAFT_RENDERERS["pattachitra"] = draw_pattachitra


def draw_bagru(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    columns = max(3, int(width / 150))
    rows = max(4, int(height / 160))
    cell_w = width / columns
    cell_h = height / rows
    for row in range(rows):
        for column in range(columns):
            offset = cell_w * 0.5 if row % 2 else 0
            cx = x1 + cell_w * (column + 0.5) + offset
            cy = y1 + cell_h * (row + 0.5)
            if cx > x2:
                cx -= width
            w = cell_w * rng.uniform(0.40, 0.53)
            h = cell_h * rng.uniform(0.30, 0.42)
            if rng.random() < 0.55:
                _buta(
                    draw, cx + rng.uniform(-5, 5), cy + rng.uniform(-4, 4),
                    w, h, _rgba(palette["indigo"]), _rgba(palette["indigo"]),
                )
                _buta(
                    draw, cx + rng.uniform(2, 7), cy + rng.uniform(2, 6),
                    w * 0.94, h * 0.94, _rgba(palette["ochre"], 210),
                    _rgba(palette["pale"]),
                )
            else:
                _flower(
                    draw, cx, cy, min(w, h) * 0.32,
                    _rgba(palette["ochre"]), _rgba(palette["indigo"]), petals=6,
                )
                draw.ellipse(
                    (cx - 5, cy - 5, cx + 5, cy + 5), fill=_rgba(palette["madder"]),
                )
    for y in (y1 + 18, y2 - 22):
        draw.line((x1 + 18, y, x2 - 18, y), fill=_rgba(palette["indigo"]), width=6)
        draw.line(
            (x1 + 18, y + 12, x2 - 18, y + 12), fill=_rgba(palette["ochre"]), width=3,
        )
    for _ in range(52):
        cx = rng.uniform(x1 + 20, x2 - 20)
        cy = rng.uniform(y1 + 20, y2 - 20)
        radius = rng.uniform(1.5, 3.5)
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=_rgba(palette["madder"], 210),
        )


CRAFT_RENDERERS["bagru-block-print"] = draw_bagru


def draw_bandhani(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    for y in range(y1, y2, 40):
        draw.line((x1, y, x2, y), fill=_rgba(palette["deep"], 34), width=1)
    columns = max(7, int(width / 80))
    rows = max(9, int(height / 90))
    for row in range(rows):
        for column in range(columns):
            offset = (width / columns) * 0.5 if row % 2 else 0
            cx = x1 + (column + 0.55) * width / columns + offset
            cy = y1 + (row + 0.55) * height / rows
            if cx > x2 - 10:
                cx -= width - 20
            radius = rng.uniform(4.0, 7.0)
            draw.ellipse(
                (cx - radius * 1.9, cy - radius * 1.9,
                 cx + radius * 1.9, cy + radius * 1.9),
                outline=_rgba(palette["white"], 235), width=2,
            )
            draw.ellipse(
                (cx - radius, cy - radius, cx + radius, cy + radius),
                fill=_rgba(palette["yellow"]),
            )
            if rng.random() < 0.30:
                for dx, dy in ((-radius * 2.1, 0), (radius * 2.1, 0), (0, -radius * 2.1)):
                    draw.ellipse(
                        (cx + dx - radius * 0.45, cy + dy - radius * 0.45,
                         cx + dx + radius * 0.45, cy + dy + radius * 0.45),
                        fill=_rgba(palette["white"]),
                    )
    for y in (y1 + 24, y1 + 46, y2 - 46, y2 - 24):
        draw.line((x1, y, x2, y), fill=_rgba(palette["yellow"]), width=4)
    for x in (x1 + 24, x1 + 46, x2 - 46, x2 - 24):
        draw.line((x, y1, x, y2), fill=_rgba(palette["yellow"]), width=4)
    for _ in range(16):
        cx = rng.uniform(x1 + 25, x2 - 25)
        cy = rng.uniform(y1 + 25, y2 - 25)
        radius = rng.uniform(18, 32)
        draw.arc(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            rng.uniform(0, 180), rng.uniform(190, 350),
            fill=_rgba(palette["pink"], 150), width=2,
        )


CRAFT_RENDERERS["bandhani"] = draw_bandhani


def draw_phulkari(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    size = max(54, int(min(width, height) / 7))
    colours = [
        _rgba(palette["yellow"]), _rgba(palette["orange"]),
        _rgba(palette["cream"]), _rgba(palette["pink"]), _rgba(palette["green"]),
    ]
    for row, cy in enumerate(range(y1 + size // 2, y2, size)):
        for column, cx in enumerate(range(x1 + size // 2, x2, size)):
            offset = size // 2 if row % 2 else 0
            cx += offset
            if cx > x2:
                cx -= width
            choice = colours[(row + column + rng.randint(0, 2)) % len(colours)]
            _diamond(draw, cx, cy, size * rng.uniform(0.36, 0.48), [choice, colours[2]], width=3)
            if rng.random() < 0.55:
                step = max(4, size // 8)
                for offset_line in range(-size // 3, size // 3, step):
                    draw.line(
                        (cx + offset_line, cy - size * 0.22,
                         cx + offset_line, cy + size * 0.22),
                        fill=colours[1], width=2,
                    )
    for y in range(y1, y2, 8):
        if rng.random() < 0.30:
            draw.line(
                (x1 + rng.uniform(0, width * 0.2), y,
                 x2 - rng.uniform(0, width * 0.2), y),
                fill=_rgba(palette["yellow"], 26), width=1,
            )
    for x in range(x1, x2, size):
        draw.line((x, y1, x, y2), fill=_rgba(palette["deep"], 70), width=1)
    for y in range(y1, y2, size):
        draw.line((x1, y, x2, y), fill=_rgba(palette["deep"], 34), width=1)


CRAFT_RENDERERS["phulkari"] = draw_phulkari


def draw_kantha(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    columns = 3
    rows = 4
    block_w = width / columns
    block_h = height / rows
    block_colours = [
        _rgba(palette["cream"]), _rgba(palette["soft"]),
        _rgba(palette["yellow"], 150), _rgba(palette["red"], 110),
        _rgba(palette["indigo"], 70),
    ]
    for row in range(rows):
        for column in range(columns):
            bx1 = x1 + column * block_w
            by1 = y1 + row * block_h
            bx2 = bx1 + block_w
            by2 = by1 + block_h
            draw.rectangle(
                (bx1, by1, bx2, by2),
                fill=rng.choice(block_colours),
            )
            draw.line((bx1, by1, bx2, by1), fill=_rgba(palette["indigo"], 80), width=2)
            draw.line((bx1, by1, bx1, by2), fill=_rgba(palette["indigo"], 80), width=2)
    for row in range(rows):
        for y in range(int(y1 + row * block_h + 30), int(y1 + (row + 1) * block_h), 34):
            phase = rng.uniform(0, math.tau)
            amplitude = rng.uniform(5, 13)
            points = []
            for x in range(int(x1 + 20), int(x2 - 20), 8):
                points.append((x, y + math.sin(x / 55 + phase) * amplitude))
            for index in range(0, len(points) - 1, 2):
                draw.line(
                    (points[index], points[index + 1]),
                    fill=rng.choice([_rgba(palette["indigo"]), _rgba(palette["red"])]),
                    width=2,
                )
    for _ in range(6):
        cx = rng.uniform(x1 + 60, x2 - 60)
        cy = rng.uniform(y1 + 60, y2 - 60)
        _flower(
            draw, cx, cy, rng.uniform(16, 30),
            _rgba(palette["yellow"]), _rgba(palette["red"]), petals=5,
        )
    for x in range(int(x1 + 40), int(x2 - 30), 65):
        draw.line((x, y2 - 40, x + 25, y2 - 10), fill=_rgba(palette["red"], 120), width=2)


CRAFT_RENDERERS["kantha"] = draw_kantha


def draw_channapatna(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    colours = [
        _rgba(palette["red"]), _rgba(palette["yellow"]),
        _rgba(palette["green"]), _rgba(palette["indigo"]),
        _rgba(palette["cream"]), _rgba(palette["wood"]),
    ]
    y = y1
    index = 0
    while y < y2:
        band = rng.randint(38, 78)
        draw.rectangle((x1, y, x2, min(y2, y + band)), fill=colours[index % len(colours)])
        if rng.random() < 0.6:
            draw.line(
                (x1, min(y2, y + band) - 4, x2, min(y2, y + band) - 4),
                fill=_rgba(palette["wood"], 150), width=2,
            )
        y += band
        index += 1
    for _ in range(22):
        cx = rng.uniform(x1 + 20, x2 - 20)
        cy = rng.uniform(y1 + 20, y2 - 20)
        radius = rng.uniform(4, 10)
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=_rgba(palette["cream"], 220),
        )
    for x in range(int(x1 + 18), int(x2 - 18), 56):
        draw.line((x, y1, x, y2), fill=_rgba(palette["wood"], 18), width=1)


CRAFT_RENDERERS["channapatna-toys"] = draw_channapatna


def draw_dhokra(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    for _ in range(12):
        cx = rng.uniform(x1 + 50, x2 - 50)
        cy = rng.uniform(y1 + 50, y2 - 50)
        _spiral(
            draw, cx, cy, rng.uniform(35, min(width, height) * 0.17),
            _rgba(palette["brass"], 230), width=rng.randint(2, 4),
            turns=rng.uniform(2.2, 3.6),
        )
    for _ in range(4):
        _tribal_figure(
            draw,
            rng.uniform(x1 + width * 0.15, x2 - width * 0.15),
            rng.uniform(y1 + height * 0.25, y2 - height * 0.20),
            height * rng.uniform(0.16, 0.25),
            _rgba(palette["gold"]),
        )
    for _ in range(70):
        cx = rng.uniform(x1 + 15, x2 - 15)
        cy = rng.uniform(y1 + 15, y2 - 15)
        radius = rng.uniform(1.5, 5)
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=_rgba(rng.choice([palette["brass"], palette["patina"], palette["cream"]])),
        )
    draw.rectangle(_inset(box, 18), outline=_rgba(palette["gold"], 190), width=4)
    draw.rectangle(_inset(box, 32), outline=_rgba(palette["brass"], 130), width=2)


CRAFT_RENDERERS["dhokra"] = draw_dhokra


def draw_blue_pottery(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    draw.rectangle(_inset(box, 16), outline=_rgba(palette["cobalt"]), width=5)
    draw.rectangle(_inset(box, 28), outline=_rgba(palette["turquoise"]), width=2)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    radius = min(width, height) * 0.21
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=_rgba(palette["cream"]), outline=_rgba(palette["cobalt"]), width=5,
    )
    _flower(
        draw, cx, cy, radius * 0.82,
        _rgba(palette["cobalt"]), _rgba(palette["yellow"]), petals=10,
    )
    _flower(
        draw, cx, cy, radius * 0.47,
        _rgba(palette["turquoise"]), _rgba(palette["cream"]), petals=8,
    )
    draw.ellipse(
        (cx - radius * 0.16, cy - radius * 0.16,
         cx + radius * 0.16, cy + radius * 0.16),
        fill=_rgba(palette["cobalt"]),
    )
    for _ in range(9):
        fx = rng.uniform(x1 + 55, x2 - 55)
        fy = rng.uniform(y1 + 55, y2 - 55)
        if math.hypot(fx - cx, fy - cy) < radius * 1.35:
            continue
        _flower(
            draw, fx, fy, min(width, height) * rng.uniform(0.035, 0.065),
            _rgba(rng.choice([palette["cobalt"], palette["turquoise"]])),
            _rgba(palette["yellow"]), petals=6,
        )
    for _ in range(20):
        lx = rng.uniform(x1 + 35, x2 - 35)
        ly = rng.uniform(y1 + 35, y2 - 35)
        _leaf(
            draw, lx, ly, rng.uniform(16, 30), rng.uniform(28, 52),
            _rgba(palette["pale"]), _rgba(palette["turquoise"]),
            angle=rng.uniform(-1.2, 1.2),
        )
    for _ in range(36):
        cx_dot = rng.uniform(x1 + 22, x2 - 22)
        cy_dot = rng.uniform(y1 + 22, y2 - 22)
        draw.ellipse(
            (cx_dot - 3, cy_dot - 3, cx_dot + 3, cy_dot + 3),
            fill=_rgba(palette["cobalt"]),
        )


CRAFT_RENDERERS["blue-pottery"] = draw_blue_pottery


def draw_generic(draw, box, rng, palette):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    draw.rectangle(box, fill=_rgba(palette["base"]))
    draw.rectangle(_inset(box, 24), outline=_rgba(palette["ink"]), width=4)
    size = max(40, int(min(width, height) / 8))
    for row, cy in enumerate(range(y1 + size, y2 - size // 2, size)):
        for column, cx in enumerate(range(x1 + size, x2 - size // 2, size)):
            _flower(
                draw, cx, cy, size * 0.34,
                _rgba(palette.get("red", palette["ink"])),
                _rgba(palette.get("gold", palette.get("cream", "#FBF5E9"))),
                petals=6,
            )


def _palette_for(craft_slug, rng):
    variants = CRAFT_PALETTES.get(craft_slug)
    if not variants:
        variants = [{
            "base": "#F1E4CE", "ink": "#2B2B2B", "red": "#B5482A",
            "gold": "#E3A018", "cream": "#FBF5E9",
            "backdrop": ("#F7EEDD", "#D2BFA1"),
        }]
    return dict(rng.choice(variants))


def product_kind(title, category=""):
    """Map a product title to one of the drawn item silhouettes."""
    import re

    text = f"{title} {category}".lower()
    words = set(re.findall(r"[a-z0-9]+", text))
    if "bookmark" in words or "bookmarks" in words:
        return "bookmarks"
    if "scroll" in words:
        return "scroll"
    if "cushion" in words or "cushions" in words:
        return "cushion"
    if "tote" in words or "bag" in words:
        return "tote"
    if "bowl" in words or "bowls" in words:
        return "bowl"
    if "tile" in words or "tiles" in words:
        return "tiles"
    if "pouch" in words or "pouches" in words:
        return "pouch"
    if "rattle" in words:
        return "rattle"
    if "spinning" in words and "top" in words:
        return "spinning_top"
    if "scarf" in words:
        return "scarf"
    if "stole" in words:
        return "stole"
    if "dupatta" in words:
        return "dupatta"
    if "elephant" in words or "figurine" in words:
        return "elephant"
    if {"painting", "panel", "wall"} & words:
        return "wall_hanging"
    return "panel"


def _build_shape(kind, size, rng):
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    geometry = {"kind": kind}
    if kind == "wall_hanging":
        box = (190, 320, 1010, 1210)
        draw.rounded_rectangle(box, radius=12, fill=255)
        geometry["box"] = box
    elif kind == "bookmarks":
        strips = []
        strip_width = 190
        gap = 55
        start = (width - (strip_width * 3 + gap * 2)) / 2
        for index in range(3):
            x1 = start + index * (strip_width + gap)
            box = (x1, 300 + index * 35, x1 + strip_width, 1220 - index * 20)
            draw.rounded_rectangle(box, radius=8, fill=255)
            strips.append(box)
        geometry["strips"] = strips
        geometry["box"] = (
            min(strip[0] for strip in strips), min(strip[1] for strip in strips),
            max(strip[2] for strip in strips), max(strip[3] for strip in strips),
        )
    elif kind == "scroll":
        box = (300, 260, 900, 1240)
        draw.rounded_rectangle(box, radius=40, fill=255)
        geometry["box"] = box
    elif kind == "cushion":
        box = (230, 390, 970, 1130)
        draw.rounded_rectangle(box, radius=55, fill=255)
        geometry["box"] = box
    elif kind == "tote":
        box = (300, 620, 900, 1260)
        draw.polygon(
            [(330, 620), (870, 620), (940, 1260), (260, 1260)],
            fill=255,
        )
        geometry["box"] = box
    elif kind == "bowl":
        box = (230, 580, 970, 1190)
        draw.ellipse(box, fill=255)
        geometry["box"] = box
    elif kind == "tiles":
        first = (190, 420, 650, 880)
        second = (550, 580, 1010, 1040)
        draw.rounded_rectangle(first, radius=12, fill=255)
        draw.rounded_rectangle(second, radius=12, fill=255)
        geometry["tiles"] = [first, second]
        geometry["box"] = (
            min(tile[0] for tile in geometry["tiles"]), min(tile[1] for tile in geometry["tiles"]),
            max(tile[2] for tile in geometry["tiles"]), max(tile[3] for tile in geometry["tiles"]),
        )
    elif kind == "pouch":
        box = (320, 560, 880, 1200)
        draw.rounded_rectangle(box, radius=65, fill=255)
        geometry["box"] = box
    elif kind == "spinning_top":
        points = [
            (600, 300), (650, 470), (930, 700), (1020, 900),
            (880, 1110), (600, 1180), (320, 1110), (180, 900),
            (270, 700), (550, 470),
        ]
        draw.polygon(points, fill=255)
        draw.ellipse((510, 250, 690, 410), fill=255)
        geometry["box"] = (180, 250, 1020, 1180)
    elif kind == "rattle":
        draw.ellipse((340, 400, 860, 920), fill=255)
        draw.rounded_rectangle((545, 880, 655, 1300), radius=45, fill=255)
        draw.rounded_rectangle((480, 930, 720, 990), radius=25, fill=255)
        draw.rounded_rectangle((470, 1080, 730, 1135), radius=22, fill=255)
        geometry["box"] = (340, 400, 860, 1300)
    elif kind == "stole":
        box = (300, 250, 900, 1270)
        _draw_fabric(draw, box, rng, wide=0.82)
        geometry["box"] = box
    elif kind == "scarf":
        box = (390, 260, 810, 1260)
        _draw_fabric(draw, box, rng, wide=0.58)
        geometry["box"] = box
    elif kind == "dupatta":
        box = (250, 280, 950, 1240)
        _draw_fabric(draw, box, rng, wide=0.94)
        geometry["box"] = box
    elif kind == "elephant":
        _draw_elephant(draw, rng)
        geometry["box"] = (160, 480, 1040, 1320)
    else:
        box = (220, 330, 980, 1180)
        draw.rounded_rectangle(box, radius=42, fill=255)
        geometry["box"] = box
        geometry["kind"] = "panel"
    return mask, geometry


def _draw_fabric(draw, box, rng, wide=0.8):
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    left = []
    right = []
    steps = 40
    phase = rng.uniform(0, math.tau)
    for index in range(steps + 1):
        ratio = index / steps
        y = y1 + height * ratio
        wave = math.sin(ratio * math.tau * 2.2 + phase) * width * 0.055
        edge = (1 - wide) * width * 0.5
        left.append((x1 + edge + wave * 0.5, y))
        right.append((x2 - edge + wave * 0.5, y))
    points = left + list(reversed(right))
    draw.polygon(points, fill=255)
    for edge in (left, right):
        draw.line(edge, fill=255, width=24, joint="curve")


def _draw_elephant(draw, rng):
    body = (360, 700, 930, 1130)
    draw.ellipse(body, fill=255)
    head = (230, 620, 560, 980)
    draw.ellipse(head, fill=255)
    ear = (330, 660, 560, 940)
    draw.ellipse(ear, fill=255)
    trunk_points = [
        (280, 860), (250, 980), (215, 1100), (205, 1220),
        (250, 1280), (310, 1250), (330, 1140), (360, 1000),
    ]
    draw.line(trunk_points, fill=255, width=92, joint="curve")
    draw.ellipse((205, 1190, 325, 1290), fill=255)
    for leg_x in (420, 570, 720, 840):
        draw.rounded_rectangle((leg_x, 1020, leg_x + 90, 1270), radius=24, fill=255)


def _draw_cover_shape(kind, size):
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    margin = int(width * 0.075)
    box = (margin, margin, width - margin, height - margin)
    if kind == "circle":
        draw.ellipse(box, fill=255)
    elif kind == "arch":
        draw.rounded_rectangle(box, radius=int(width * 0.34), fill=255)
        draw.rectangle((margin, height // 2, width - margin, height - margin), fill=255)
    else:
        draw.rounded_rectangle(box, radius=int(width * 0.10), fill=255)
    return mask, box


def _item_shade(size, mask, palette, glossy=False):
    width, height = size
    shade = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shade)
    draw.rectangle((0, height * 0.64, width, height), fill=(25, 16, 10, 55))
    if glossy:
        draw.ellipse(
            (width * 0.18, height * 0.15, width * 0.62, height * 0.46),
            fill=(255, 250, 235, 85),
        )
    shade = shade.filter(ImageFilter.GaussianBlur(width * 0.035))
    shade.putalpha(ImageChops.multiply(shade.getchannel("A"), mask))
    return shade


def _outline(size, mask, colour, width=3):
    edge = mask.filter(ImageFilter.FIND_EDGES)
    edge = edge.filter(ImageFilter.MaxFilter(max(3, width * 2 + 1)))
    layer = Image.new("RGBA", size, _rgba(colour, 210))
    layer.putalpha(edge)
    return layer


def _shadow(size, mask, offset=(0, 34), blur=34, opacity=0.42):
    width, height = size
    shifted = Image.new("L", size, 0)
    blurred = mask.filter(ImageFilter.GaussianBlur(blur))
    shifted.paste(blurred, offset)
    shifted = shifted.point(lambda value: int(value * opacity))
    layer = Image.new("RGBA", size, (42, 28, 18, 255))
    layer.putalpha(shifted)
    return layer


def _draw_item_details(image, geometry, palette, rng):
    size = image.size
    width, height = size
    draw = ImageDraw.Draw(image, "RGBA")
    kind = geometry["kind"]
    box = geometry.get("box")
    if kind == "wall_hanging":
        x1, y1, x2, y2 = box
        rod_y = y1 - 55
        draw.line((x1 - 45, rod_y, x2 + 45, rod_y), fill=_rgba("#6B4426"), width=18)
        for x in (x1 - 45, x2 + 45):
            draw.ellipse((x - 16, rod_y - 16, x + 16, rod_y + 16), fill=_rgba("#6B4426"))
        for x in (x1 + 75, x2 - 75):
            draw.line((x, rod_y, x, y1 + 20), fill=_rgba("#7A5A39"), width=4)
        draw.rectangle(_inset(box, 6), outline=_rgba(palette["ink"], 120), width=2)
        for x in range(int(x1 + 18), int(x2 - 10), 38):
            draw.line((x, y2 + 2, x, y2 + 28), fill=_rgba(palette["ink"], 200), width=3)
            draw.ellipse((x - 4, y2 + 24, x + 4, y2 + 34), fill=_rgba(palette["gold"]))
    elif kind == "bookmarks":
        for index, strip in enumerate(geometry["strips"]):
            x1, y1, x2, y2 = strip
            draw.rounded_rectangle(_inset(strip, 5), radius=5, outline=_rgba(palette["ink"], 150), width=2)
            tassel_y = y1 - 34
            draw.line((x1 + 35, y1, x1 + 35, tassel_y), fill=_rgba(palette["gold"]), width=3)
            draw.line((x2 - 35, y1, x2 - 35, tassel_y), fill=_rgba(palette["gold"]), width=3)
            draw.ellipse((x1 + 25, tassel_y - 8, x1 + 45, tassel_y + 12), fill=_rgba(palette["gold"]))
            draw.ellipse((x2 - 45, tassel_y - 8, x2 - 25, tassel_y + 12), fill=_rgba(palette["gold"]))
    elif kind == "scroll":
        x1, y1, x2, y2 = box
        for top in (y1, y2 - 60):
            draw.rounded_rectangle((x1 - 35, top, x2 + 35, top + 60), radius=24, fill=_rgba(palette["gold"]))
            draw.line((x1 - 20, top + 16, x2 + 20, top + 16), fill=_rgba(palette["cream"], 170), width=2)
            draw.ellipse((x1 - 40, top + 18, x1 - 25, top + 42), fill=_rgba(palette["ink"], 170))
            draw.ellipse((x2 + 25, top + 18, x2 + 40, top + 42), fill=_rgba(palette["ink"], 170))
    elif kind == "cushion":
        x1, y1, x2, y2 = box
        draw.rounded_rectangle(_inset(box, 14), radius=44, outline=_rgba(palette["ink"], 120), width=2)
        for cx, cy in ((x1, y1), (x2, y1), (x1, y2), (x2, y2)):
            draw.line((cx, cy, cx + (18 if cx == x1 else -18), cy + (18 if cy == y1 else -18)),
                      fill=_rgba(palette["gold"]), width=4)
            draw.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=_rgba(palette["gold"]))
        draw.line((x1 + 30, (y1 + y2) / 2, x2 - 30, (y1 + y2) / 2), fill=_rgba(palette["ink"], 55), width=2)
    elif kind == "tote":
        x1, y1, x2, y2 = box
        for side in (-1, 1):
            centre = (x1 + x2) / 2 + side * 190
            draw.arc((centre - 150, y1 - 270, centre + 150, y1 + 60), 180, 360,
                     fill=_rgba("#6B4426"), width=18)
        draw.line((x1 + 30, y1 + 50, x2 - 30, y1 + 50), fill=_rgba(palette["ink"], 75), width=8)
        for x in range(int(x1 + 35), int(x2 - 20), 42):
            draw.line((x, y1 + 30, x, y1 + 70), fill=_rgba(palette["gold"], 160), width=2)
    elif kind == "bowl":
        x1, y1, x2, y2 = box
        rim = (x1 - 18, y1 - 55, x2 + 18, y1 + 210)
        draw.ellipse(rim, fill=_rgba(palette["cream"]), outline=_rgba(palette["ink"], 190), width=5)
        draw.ellipse(
            (x1 + 72, y1 + 5, x2 - 72, y1 + 130),
            fill=_rgba(palette["ink"], 105),
            outline=_rgba(palette["gold"], 150), width=3,
        )
    elif kind == "tiles":
        for box_tile in geometry["tiles"]:
            draw.rounded_rectangle(box_tile, radius=12, outline=_rgba(palette["ink"], 180), width=4)
            draw.rounded_rectangle(_inset(box_tile, 10), radius=8, outline=_rgba(palette["gold"], 180), width=2)
    elif kind == "pouch":
        x1, y1, x2, y2 = box
        draw.line((x1 + 30, y1 + 95, x2 - 30, y1 + 95), fill=_rgba(palette["ink"], 200), width=5)
        draw.arc((x1 + 30, y1 + 60, x2 - 30, y1 + 130), 180, 360,
                 fill=_rgba(palette["gold"]), width=4)
        for side in (-1, 1):
            cx = (x1 + x2) / 2 + side * 70
            draw.line((cx, y1 + 95, cx + side * 12, y1 + 170), fill=_rgba(palette["gold"]), width=4)
            draw.ellipse((cx + side * 12 - 8, y1 + 162, cx + side * 12 + 8, y1 + 182),
                         fill=_rgba(palette["gold"]))
        draw.rounded_rectangle(_inset(box, 10), radius=58, outline=_rgba(palette["ink"], 130), width=2)
    elif kind == "spinning_top":
        x1, y1, x2, y2 = box
        draw.ellipse((width / 2 - 85, y1 + 10, width / 2 + 85, y1 + 160),
                     outline=_rgba(palette["ink"], 170), width=8)
        draw.line((width / 2, y1 + 130, width / 2, y1 + 230), fill=_rgba("#7A4D2A"), width=26)
        draw.arc((x1 + 90, y2 - 300, x2 - 90, y2 - 40), 10, 170,
                 fill=_rgba(palette["cream"], 140), width=10)
        for y in range(int(y1 + 240), int(y2 - 80), 70):
            draw.line((width / 2 - (y - y1) * 0.12, y, width / 2 + (y - y1) * 0.12, y),
                      fill=_rgba(palette["ink"], 45), width=2)
    elif kind == "rattle":
        x1, y1, x2, y2 = box
        draw.ellipse((x1, y1, x2, y1 + 520), outline=_rgba(palette["ink"], 190), width=4)
        draw.ellipse((width / 2 - 34, y1 + 90, width / 2 + 34, y1 + 170),
                     fill=_rgba(palette["cream"], 130))
        for ring_y in (940, 1000, 1080):
            draw.ellipse((470, ring_y - 18, 730, ring_y + 52),
                         outline=_rgba(palette["gold"]), width=10)
        draw.line((width / 2, 880, width / 2, 1300), fill=_rgba("#7A4D2A", 170), width=8)
        draw.ellipse((width / 2 - 18, 1280, width / 2 + 18, 1316), fill=_rgba("#7A4D2A"))
    elif kind in {"stole", "dupatta", "scarf"}:
        x1, y1, x2, y2 = box
        for index in range(3):
            offset = (index + 1) / 4
            base_y = y1 + (y2 - y1) * offset
            points = []
            for step in range(9):
                ratio = step / 8
                points.append((
                    x1 + 45 + (x2 - x1 - 90) * ratio,
                    base_y + math.sin(ratio * math.pi * 2 + index) * 12,
                ))
            draw.line(points, fill=_rgba(palette["ink"], 18), width=4, joint="curve")
        for y in (y1 + 4, y2 - 4):
            for x in range(int(x1 + 60), int(x2 - 40), 26):
                draw.line((x, y, x + rng.uniform(-5, 5), y + (45 if y == y2 - 4 else -45)),
                          fill=_rgba(palette["gold"], 180), width=2)
    elif kind == "elephant":
        draw.ellipse((286, 742, 322, 778), fill=_rgba(palette["cream"]))
        draw.ellipse((298, 750, 312, 768), fill=_rgba(palette["ink"]))
        draw.line(
            [(285, 900), (235, 926), (198, 950), (212, 970), (268, 948), (320, 916)],
            fill=_rgba(palette["cream"], 225), width=14, joint="curve",
        )
        draw.ellipse((192, 943, 206, 957), fill=_rgba(palette["cream"], 235))
        draw.arc((335, 660, 560, 940), 200, 330, fill=_rgba(palette["gold"], 150), width=6)
        draw.ellipse((388, 744, 432, 792), outline=_rgba(palette["gold"], 150), width=3)
        draw.line(
            [(935, 880), (1010, 930), (1040, 990), (1018, 1045)],
            fill=_rgba(palette["ink"], 220), width=7, joint="curve",
        )
        draw.polygon([(1008, 1038), (1010, 1072), (1032, 1050)], fill=_rgba(palette["ink"], 220))
    elif kind == "panel":
        draw.rounded_rectangle(_inset(box, 12), radius=34, outline=_rgba(palette["ink"], 150), width=4)


def _save_jpeg(image, path, quality=85, limit=JPEG_LIMIT):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image = image.convert("RGB")
    for attempt_quality in (quality, 84, 82, 80, 78, 75, 70, 65, 60, 55):
        buffer = BytesIO()
        image.save(
            buffer, format="JPEG", quality=attempt_quality,
            optimize=True, progressive=True, subsampling=2,
        )
        if buffer.tell() <= limit:
            path.write_bytes(buffer.getvalue())
            return path
    raise ValueError(f"Could not keep {path.name} under {limit} bytes at the requested size")


def product_art(slug, craft_slug, title, category="", size=CANVAS):
    """Return the deterministic RGBA artwork for one product."""
    if size != CANVAS:
        raise ValueError("Product artwork is fixed at 1200x1500")
    rng = random.Random(f"virasat-product|{slug}|{craft_slug}")
    palette = _palette_for(craft_slug, rng)
    canvas = _paper_backdrop(size, palette, rng)
    kind = product_kind(title, category)
    mask, geometry = _build_shape(kind, size, rng)
    x1, y1, x2, y2 = geometry["box"]
    pattern_box = tuple(int(value) for value in geometry["box"])
    if kind == "bowl":
        pattern_box = (x1 + 36, y1 + 158, x2 - 36, y2 - 18)
    pattern = Image.new("RGBA", size, (0, 0, 0, 0))
    pattern_draw = ImageDraw.Draw(pattern)
    renderer = CRAFT_RENDERERS.get(craft_slug, draw_generic)
    renderer(pattern_draw, pattern_box, rng, palette)
    pattern.putalpha(ImageChops.multiply(pattern.getchannel("A"), mask))

    canvas.alpha_composite(_shadow(size, mask))
    canvas.alpha_composite(pattern)
    canvas.alpha_composite(_item_shade(size, mask, palette, glossy=craft_slug in {
        "channapatna-toys", "blue-pottery", "dhokra",
    }))
    _draw_item_details(canvas, geometry, palette, rng)
    canvas.alpha_composite(_outline(size, mask, palette.get("ink", palette["base"]), width=2))
    canvas = _vignette(canvas)
    return canvas


def craft_art(craft_slug, craft_name, size=COVER_SIZE):
    """Return deterministic square cover art for one craft tradition."""
    rng = random.Random(f"virasat-craft|{craft_slug}|{craft_name}")
    palette = _palette_for(craft_slug, rng)
    canvas = _paper_backdrop(size, palette, rng)
    if craft_slug in {"madhubani", "pattachitra"}:
        cover_kind = "arch"
    else:
        cover_kind = "panel"
    mask, box = _draw_cover_shape(cover_kind, size)
    pattern = Image.new("RGBA", size, (0, 0, 0, 0))
    pattern_draw = ImageDraw.Draw(pattern)
    renderer = CRAFT_RENDERERS.get(craft_slug, draw_generic)
    renderer(pattern_draw, box, rng, palette)
    pattern.putalpha(ImageChops.multiply(pattern.getchannel("A"), mask))
    canvas.alpha_composite(_shadow(size, mask, offset=(0, 22), blur=28, opacity=0.38))
    canvas.alpha_composite(pattern)
    canvas.alpha_composite(_item_shade(size, mask, palette, glossy=craft_slug in {
        "channapatna-toys", "blue-pottery", "dhokra",
    }))
    canvas.alpha_composite(_outline(size, mask, palette.get("ink", palette["base"]), width=2))
    draw = ImageDraw.Draw(canvas, "RGBA")
    for x, y in ((28, 28), (size[0] - 28, 28), (28, size[1] - 28), (size[0] - 28, size[1] - 28)):
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=_rgba(palette.get("gold", "#E3A018")))
    return _vignette(canvas)


def save_product_image(path, slug, craft_slug, title, category=""):
    """Render and save one product JPEG, returning the path."""
    return _save_jpeg(product_art(slug, craft_slug, title, category), path, quality=85)


def save_craft_image(path, craft_slug, craft_name):
    """Render and save one square craft JPEG, returning the path."""
    return _save_jpeg(craft_art(craft_slug, craft_name), path, quality=85, limit=180 * 1024)


def import_seed_photo(source, destination):
    """Crop an owned seed photo to 4:5, compress it, and write it to media."""
    source = Path(source)
    destination = Path(destination)
    with Image.open(source) as image:
        image = image.convert("RGB")
        image = ImageOps.fit(image, CANVAS, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    return _save_jpeg(image, destination, quality=85)
