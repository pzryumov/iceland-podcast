#!/usr/bin/env python3
"""Generate a 1500x1500 podcast cover: 'FIRE & ICE' over a relief map of Iceland.
Run with: uv run --with pillow python make_cover.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 1500
MAP = "_map.jpg"
OUT = "cover.jpg"

FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"
ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def load_font(size, want="bold"):
    """Prefer a heavy Futura face; fall back to Arial Bold."""
    try:
        best = None
        for i in range(0, 12):
            try:
                f = ImageFont.truetype(FUTURA, size, index=i)
            except Exception:
                break
            name = " ".join(f.getname()).lower()
            if want == "bold" and ("extrabold" in name or "extra bold" in name):
                return f
            if want == "bold" and "bold" in name and best is None:
                best = f
            if want == "medium" and "medium" in name and "condensed" not in name:
                return f
        if best:
            return best
    except Exception:
        pass
    return ImageFont.truetype(ARIAL_BOLD, size)


def main():
    # --- base: Iceland map sitting in its own sea, on a square canvas ---
    m = Image.open(MAP).convert("RGB")
    sea = m.getpixel((6, 6))  # light-blue sea sample
    canvas = Image.new("RGB", (S, S), sea)
    w = S
    h = round(m.height * S / m.width)
    m2 = m.resize((w, h), Image.LANCZOS)
    canvas.paste(m2, (0, (S - h) // 2))

    # --- top "night sky" scrim (dark, fading down) for title legibility ---
    top = Image.new("L", (1, S), 0)
    for y in range(S):
        if y < int(S * 0.46):
            a = int(205 * (1 - y / (S * 0.46)) ** 1.15)
        else:
            a = 0
        top.putpixel((0, y), a)
    top = top.resize((S, S))
    navy = Image.new("RGB", (S, S), (8, 26, 48))
    canvas = Image.composite(navy, canvas, top)

    # --- bottom scrim for subtitle/credit ---
    bot = Image.new("L", (1, S), 0)
    for y in range(S):
        if y > int(S * 0.74):
            a = int(170 * ((y - S * 0.74) / (S * 0.26)) ** 1.2)
        else:
            a = 0
        bot.putpixel((0, y), a)
    bot = bot.resize((S, S))
    canvas = Image.composite(Image.new("RGB", (S, S), (8, 22, 40)), canvas, bot)

    draw = ImageDraw.Draw(canvas)

    # --- title: FIRE & ICE ---
    title_font = load_font(232, "bold")
    parts = [("FIRE", (242, 104, 26)), (" & ", (255, 255, 255)), ("ICE", (96, 200, 240))]
    widths = [draw.textlength(t, font=title_font) for t, _ in parts]
    total = sum(widths)
    x = (S - total) / 2
    ty = 150
    # soft drop shadow
    for t, _ in parts:
        pass
    xs = x
    for (t, col), wpart in zip(parts, widths):
        draw.text((xs + 5, ty + 6), t, font=title_font, fill=(0, 0, 0))
        xs += wpart
    xs = x
    for (t, col), wpart in zip(parts, widths):
        draw.text((xs, ty), t, font=title_font, fill=col)
        xs += wpart

    # --- subtitle: letter-spaced ---
    sub_font = load_font(60, "medium")
    sub = "AN ICELAND ROAD-TRIP PODCAST"
    track = 8
    sw = sum(draw.textlength(c, font=sub_font) + track for c in sub) - track
    sx = (S - sw) / 2
    sy = ty + 250
    for c in sub:
        draw.text((sx, sy), c, font=sub_font, fill=(232, 244, 252))
        sx += draw.textlength(c, font=sub_font) + track

    # --- credit ---
    cred_font = load_font(50, "medium")
    cred = "with Anna  &  Magnus"
    cw = draw.textlength(cred, font=cred_font)
    draw.text(((S - cw) / 2, S - 130), cred, font=cred_font, fill=(214, 232, 244))

    canvas.convert("RGB").save(OUT, "JPEG", quality=92)
    print("wrote", OUT, canvas.size)


if __name__ == "__main__":
    main()
