#!/usr/bin/env python3
"""Generate the site's Open Graph cards from the repo's own design tokens.

Self-contained: no external service, no downloaded fonts. Reads the token
values from app/styles/_tokens.scss, converts the site's bundled
public/fonts/archivo-variable-latin.woff2 to TTF with fontTools, and writes
1200x630 PNGs under public/visuels/og/.

Deps: Pillow + fontTools (python3 -m pip install Pillow fonttools).
Usage:  python3 scripts/gen-og-cards.py
"""
import os
import re

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS_SCSS = os.path.join(REPO, "app", "styles", "_tokens.scss")
FONT_WOFF2 = os.path.join(REPO, "public", "fonts", "archivo-variable-latin.woff2")
FONT_TTF = os.path.join(REPO, "scripts", ".archivo-variable-latin.ttf")
OUT_DIR = os.path.join(REPO, "public", "visuels", "og")

W, H = 1200, 630


def token(name, default):
    """Read one CSS custom property from _tokens.scss (light theme values)."""
    scss = open(TOKENS_SCSS, encoding="utf-8").read()
    m = re.search(rf"--{name}:\s*([^;]+);", scss)
    return m.group(1).strip() if m else default


def hex_to_rgb(value):
    value = value.strip()
    if value.startswith("#"):
        value = value[1:]
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def load_fonts():
    """Convert the bundled variable woff2 to an instantly-loaded TTF."""
    if not os.path.exists(FONT_TTF):
        from fontTools.ttLib import TTFont

        font = TTFont(FONT_WOFF2)
        font.flavor = None  # strip WOFF2 container -> plain TTF
        font.save(FONT_TTF)
    return {
        "label": ImageFont.truetype(FONT_TTF, 34),
        "body": ImageFont.truetype(FONT_TTF, 40),
        "display": ImageFont.truetype(FONT_TTF, 96),
    }


def fit_font(font, text, max_w, min_size=30):
    f = font
    while f.size > min_size:
        bb = f.getbbox(text)
        if (bb[2] - bb[0]) <= max_w:
            return f
        f = ImageFont.truetype(f.path, f.size - 4)
    return f


def draw_center(draw, cy, text, font, fill, max_w=W - 160):
    font = fit_font(font, text, max_w)
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    draw.text(
        ((W - tw) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]),
        text,
        font=font,
        fill=fill,
    )
    return font


def card(out, eyebrow, title, subtitle, fonts, colors):
    bg, fg, muted, ink, line = colors
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    # Filet plutôt que carte : deux règles, une encre d'annotation.
    d.line([(80, 96), (W - 80, 96)], fill=line, width=2)
    d.rectangle([80, 64, 118, 102], fill=ink)
    d.text((150, 60), eyebrow.upper(), font=fonts["label"], fill=ink)
    title_font = draw_center(d, 300, title, fonts["display"], fg)
    draw_center(
        d, 300 + 60 + (title_font.size // 2) + 30, subtitle, fonts["body"], muted,
        max_w=W - 240,
    )
    d.line([(80, 486), (W - 80, 486)], fill=line, width=2)
    d.text((80, 520), "ARNAUD BRÉGÈRE", font=fonts["body"], fill=fg)
    d.text((W - 80, 520), "FRONT-END SENIOR", font=fonts["body"], fill=muted, anchor="rs")
    d.text((80, 560), "arnaud-bregere.fr", font=fonts["body"], fill=ink)
    img.save(out, "PNG")
    print("wrote", out)


def main():
    fonts = load_fonts()
    colors = (
        hex_to_rgb(token("color-bg", "#f7f4ef")),
        hex_to_rgb(token("color-fg", "#14120f")),
        hex_to_rgb(token("color-fg-muted", "#6b655c")),
        hex_to_rgb(token("color-ink", "#b3122b")),
        hex_to_rgb(token("color-line", "#d6cfc4")),
    )
    os.makedirs(OUT_DIR, exist_ok=True)
    cards = [
        ("og-accueil.png", "Accueil", "Arnaud Brégère", "Développeur front-end senior — Vue 3, Nuxt, design system"),
        ("og-a-propos.png", "À propos", "Parcours", "Six ans de Vue et Nuxt chez Figaro Classifieds"),
        ("og-contact.png", "Contact", "Écrire à Arnaud", "Disponible pour un poste de senior ou lead front-end"),
        ("og-projets.png", "Projets", "Problème, solution, résultat", "Chaque fiche porte son chiffre mesuré"),
        ("og-projet.png", "Projet", "Un problème, une solution, un résultat", "Étude de cas front-end — Vue 3, Nuxt, design system"),
    ]
    for name, eyebrow, title, subtitle in cards:
        card(os.path.join(OUT_DIR, name), eyebrow, title, subtitle, fonts, colors)


if __name__ == "__main__":
    main()
