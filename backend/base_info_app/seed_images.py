"""Offline generator for the demo seed's placeholder images.

Pure-Pillow drawing (no network, no external assets). This module is run
**locally** to (re)generate the committed PNGs under ``seed_assets/``; the
Docker image ships those PNGs, so the running server never needs Pillow or a
system font to display seed images — the seeder just copies the committed
files into ``MEDIA_ROOT``.

Regenerate the committed assets after tweaking a design:

    python base_info_app/seed_images.py      # run from the backend/ dir

Public helpers:
    render_avatar(initials, key)              -> PNG bytes (profile picture)
    render_offer_cover(title, category, sub)  -> PNG bytes (offer thumbnail)
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------- #
# Fonts — macOS ships Arial, Linux (GCP deploy) ships DejaVu; fall back to
# Pillow's bitmap font so seeding never hard-crashes on a missing font file.
# --------------------------------------------------------------------------- #
_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
# Arial Unicode / DejaVu cover the CJK "文" glyph on the translation cover.
_UNICODE_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _load_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _bold(size):
    return _load_font(_BOLD_CANDIDATES, size)


def _unicode(size):
    return _load_font(_UNICODE_CANDIDATES, size)


WHITE = (255, 255, 255)

# Per-key two-colour gradients (top-left -> bottom-right), dark enough that
# white text keeps contrast.
AVATAR_GRADIENTS = {
    "b_designer":   ((0xF8, 0x57, 0xA6), (0x7B, 0x2F, 0xF7)),  # magenta -> violet
    "b_developer":  ((0x25, 0x63, 0xEB), (0x1E, 0x3A, 0x8A)),  # blue -> indigo
    "b_translator": ((0x11, 0x99, 0x8E), (0x0B, 0x63, 0x3F)),  # teal -> green
    "b_copywriter": ((0xF7, 0x51, 0x2F), (0xDD, 0x24, 0x76)),  # orange -> pink
    "c_anna":  ((0xFF, 0x6A, 0x88), (0xC3, 0x37, 0x64)),       # rose
    "c_ben":   ((0x05, 0x75, 0xE6), (0x02, 0x1B, 0x79)),       # sky -> navy
    "c_clara": ((0xDA, 0x22, 0xFF), (0x73, 0x0F, 0xC8)),       # magenta -> purple
    "c_dario": ((0xF7, 0x97, 0x1E), (0xB0, 0x45, 0x0A)),       # amber -> brown
}
_AVATAR_FALLBACK = ((0x4B, 0x5C, 0x7A), (0x1F, 0x29, 0x37))

OFFER_GRADIENTS = {
    "design":      ((0x7B, 0x2F, 0xF7), (0xF1, 0x07, 0xA3)),
    "print":       ((0x13, 0x6A, 0x8A), (0x26, 0x78, 0x71)),
    "dev":         ((0x1D, 0x4E, 0xD8), (0x0F, 0x17, 0x2A)),
    "translation": ((0x11, 0x99, 0x8E), (0x1B, 0x6B, 0x3F)),
    "writing":     ((0xF1, 0x27, 0x11), (0xF5, 0xAF, 0x19)),
}
_OFFER_FALLBACK = ((0x33, 0x3D, 0x51), (0x17, 0x1C, 0x28))


def _diagonal_gradient(size, c1, c2):
    """Fast bilinear diagonal gradient via a 2x2 upscale."""
    w, h = size
    mid = tuple((a + b) // 2 for a, b in zip(c1, c2))
    small = Image.new("RGB", (2, 2))
    small.putpixel((0, 0), c1)
    small.putpixel((1, 0), mid)
    small.putpixel((0, 1), mid)
    small.putpixel((1, 1), c2)
    return small.resize((w, h), Image.BILINEAR)


def _centered(draw, cx, cy, text, font, fill=WHITE, shadow=True):
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    x, y = cx - tw / 2 - box[0], cy - th / 2 - box[1]
    if shadow:
        draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


def _to_png(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Avatar
# --------------------------------------------------------------------------- #
def render_avatar(initials, key, size=512):
    """Monogram avatar: diagonal gradient + big white initials + inner ring."""
    c1, c2 = AVATAR_GRADIENTS.get(key, _AVATAR_FALLBACK)
    img = _diagonal_gradient((size, size), c1, c2).convert("RGBA")

    # soft vignette so initials stay legible on lighter stops
    vign = Image.new("L", (size, size), 0)
    ImageDraw.Draw(vign).ellipse(
        [size * 0.1, size * 0.1, size * 0.9, size * 0.9], fill=60)
    shade = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shade.putalpha(vign)
    img = Image.alpha_composite(img, shade)

    draw = ImageDraw.Draw(img)
    _centered(draw, size / 2, size / 2, initials.upper(), _bold(int(size * 0.42)))
    m = int(size * 0.045)
    draw.ellipse([m, m, size - m, size - m], outline=(255, 255, 255, 70),
                 width=max(2, size // 90))
    return _to_png(img)


# --------------------------------------------------------------------------- #
# Offer cover
# --------------------------------------------------------------------------- #
def _draw_icon(d, category, w, h):
    cx, cy = w // 2, h // 2          # centred: survives object-fit cropping
    s = int(min(w, h) * 0.42)
    fill = (255, 255, 255, 235)
    soft = (255, 255, 255, 70)

    if category == "design":                       # overlapping colour swatches
        r = s // 2
        for dx, dy, a in [(-r // 2, -r // 3, 120), (r // 2, -r // 3, 120),
                          (0, r // 2, 120)]:
            d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r],
                      fill=(255, 255, 255, a))
        d.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3], fill=fill)

    elif category == "print":                      # two stacked business cards
        cw, ch = int(s * 1.15), int(s * 0.7)
        d.rounded_rectangle([cx - cw // 2 + 26, cy - ch // 2 + 26,
                             cx + cw // 2 + 26, cy + ch // 2 + 26],
                            radius=18, fill=soft)
        d.rounded_rectangle([cx - cw // 2, cy - ch // 2, cx + cw // 2,
                             cy + ch // 2], radius=18, fill=fill)
        d.ellipse([cx - cw // 2 + 26, cy - 20, cx - cw // 2 + 74, cy + 28],
                  fill=(0, 0, 0, 45))
        for i in range(3):
            yy = cy - 14 + i * 20
            d.rounded_rectangle([cx - 4, yy, cx + cw // 2 - 30, yy + 8],
                                radius=4, fill=(0, 0, 0, 45))

    elif category == "dev":                         # browser window with </>
        bw, bh = int(s * 1.25), int(s * 0.95)
        x0, y0 = cx - bw // 2, cy - bh // 2
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=18, fill=fill)
        d.rectangle([x0, y0, x0 + bw, y0 + 40], fill=(0, 0, 0, 45))
        for i, col in enumerate([(0xFF, 0x5F, 0x56), (0xFF, 0xBD, 0x2E),
                                 (0x27, 0xC9, 0x3F)]):
            d.ellipse([x0 + 20 + i * 30, y0 + 12, x0 + 36 + i * 30, y0 + 28],
                      fill=col + (255,))
        cf = _bold(int(bh * 0.5))
        cb = d.textbbox((0, 0), "</>", font=cf)
        d.text((cx - (cb[2] - cb[0]) / 2 - cb[0],
                y0 + 40 + (bh - 40) / 2 - (cb[3] - cb[1]) / 2 - cb[1]),
               "</>", font=cf, fill=(0, 0, 0, 160))

    elif category == "translation":                 # speech bubbles "A" / "文"
        bw = int(s * 0.8)
        for dx, glyph in [(-int(s * 0.35), "A"), (int(s * 0.35), "文")]:
            x0, y0 = cx + dx - bw // 2, cy - bw // 2
            d.rounded_rectangle([x0, y0, x0 + bw, y0 + bw], radius=22, fill=fill)
            d.polygon([(x0 + bw * 0.3, y0 + bw), (x0 + bw * 0.5, y0 + bw),
                       (x0 + bw * 0.32, y0 + bw + 22)], fill=fill)
            gf = _unicode(int(bw * 0.62))
            gb = d.textbbox((0, 0), glyph, font=gf)
            d.text((x0 + bw / 2 - (gb[2] - gb[0]) / 2 - gb[0],
                    y0 + bw / 2 - (gb[3] - gb[1]) / 2 - gb[1]),
                   glyph, font=gf, fill=(0x11, 0x99, 0x8E))

    elif category == "writing":                     # document + magnifier
        dw, dh = int(s * 0.9), int(s * 1.15)
        x0, y0 = cx - dw // 2 - 20, cy - dh // 2
        d.rounded_rectangle([x0, y0, x0 + dw, y0 + dh], radius=14, fill=fill)
        for i in range(5):
            yy = y0 + 34 + i * 30
            ln = dw - 44 if i % 2 == 0 else dw - 90
            d.rounded_rectangle([x0 + 24, yy, x0 + 24 + ln, yy + 10],
                                radius=5, fill=(0, 0, 0, 60))
        gr = int(s * 0.32)
        gx, gy = cx + int(s * 0.42), cy + int(s * 0.42)
        d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], outline=fill,
                  width=max(6, s // 22))
        d.line([gx + gr * 0.7, gy + gr * 0.7, gx + gr * 1.5, gy + gr * 1.5],
               fill=fill, width=max(8, s // 18))

    else:                                           # generic dot
        r = s // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def render_offer_cover(title="", category="", subtitle="", size=(1200, 750)):
    """Clean themed offer thumbnail: diagonal gradient + a centred glyph.

    Deliberately text-free: the card UI already shows the offer's title,
    author and price beneath the image, so baking them in here only
    duplicates them. ``title`` / ``subtitle`` are accepted for a stable call
    signature but no longer drawn.
    """
    w, h = size
    c1, c2 = OFFER_GRADIENTS.get(category, _OFFER_FALLBACK)
    img = _diagonal_gradient((w, h), c1, c2).convert("RGBA")

    icon = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    _draw_icon(ImageDraw.Draw(icon), category, w, h)
    return _to_png(Image.alpha_composite(img, icon))


# --------------------------------------------------------------------------- #
# Committed-asset manifest + regeneration
# --------------------------------------------------------------------------- #
# username -> initials (must match the users seeded by seed_demo_data).
DEMO_AVATARS = {
    "b_designer": "LB", "b_developer": "TY", "b_translator": "SK",
    "b_copywriter": "MS", "c_anna": "AS", "c_ben": "BH",
    "c_clara": "CW", "c_dario": "DA",
}
# (slug, title, category, subtitle). ``slug`` must equal Django's
# slugify(title) so the seeder finds the file by title.
DEMO_OFFERS = [
    ("logo-design-paket",     "Logo-Design-Paket",     "design",      "Lena Bauer"),
    ("visitenkarten-design",  "Visitenkarten-Design",  "print",       "Lena Bauer"),
    ("landingpage-in-django", "Landingpage in Django", "dev",         "Tarek Yilmaz"),
    ("fachubersetzung-deen",  "Fachübersetzung DE↔EN", "translation", "Sophie Klein"),
    ("seo-blogposts",         "SEO-Blogposts",         "writing",     "Mara Schulz"),
]


def regenerate(dest):
    """(Re)write every committed seed PNG under ``dest`` (profiles/ + offers/)."""
    dest = Path(dest)
    (dest / "profiles").mkdir(parents=True, exist_ok=True)
    (dest / "offers").mkdir(parents=True, exist_ok=True)
    for username, initials in DEMO_AVATARS.items():
        (dest / "profiles" / f"{username}.png").write_bytes(
            render_avatar(initials, username))
    for slug, title, category, subtitle in DEMO_OFFERS:
        (dest / "offers" / f"{slug}.png").write_bytes(
            render_offer_cover(title, category, subtitle=subtitle))
    return dest


if __name__ == "__main__":
    out = regenerate(Path(__file__).resolve().parent / "seed_assets")
    print(f"Regenerated seed assets in {out}")
