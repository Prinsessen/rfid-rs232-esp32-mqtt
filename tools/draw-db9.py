#!/usr/bin/env python3
"""Draws docs/DB9_MEASURE.png: DB-9 faces (male and female, seen from the front) with pins 2, 3 and 5 marked,
and how to bip a male-male cable before the reader goes on it (2026-11-22).
Run: /etc/openhab/.venv/bin/python3 tools/draw-db9.py"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "DB9_MEASURE.png")
W, H = 2000, 1500
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f = lambda s, b=False: ImageFont.truetype(FB if b else F, s)
BLACK, GREY, GREEN, BLUE, RED, ORANGE = (0, 0, 0), (130, 130, 130), (30, 160, 40), (40, 70, 200), (210, 50, 50), (225, 120, 20)
MARK = {3: (GREEN, "3"), 2: (ORANGE, "2"), 5: (BLACK, "5")}


def text(x, y, s, size=30, c=BLACK, b=False, a="la"):
    d.text((x, y), s, font=f(size, b), fill=c, anchor=a)


def db9(cx, cy, male, title, sub):
    """front view. male: pins 1-5 left->right on the wide row; female: mirrored (5..1)."""
    w1, w2, h = 520, 420, 240
    shell = [(cx - w1 // 2, cy - h // 2), (cx + w1 // 2, cy - h // 2), (cx + w2 // 2, cy + h // 2), (cx - w2 // 2, cy + h // 2)]
    d.polygon(shell, outline=BLACK, width=6, fill=(235, 235, 235))
    text(cx, cy - h // 2 - 110, title, 36, BLACK, True, "ma")
    text(cx, cy - h // 2 - 62, sub, 24, GREY, a="ma")
    top = [1, 2, 3, 4, 5] if male else [5, 4, 3, 2, 1]
    bot = [6, 7, 8, 9] if male else [9, 8, 7, 6]
    for row, pins, y in ((0, top, cy - 50), (1, bot, cy + 55)):
        n = len(pins)
        step = 90
        x0 = cx - (n - 1) * step // 2
        for i, p in enumerate(pins):
            x = x0 + i * step
            c, _ = MARK.get(p, (GREY, ""))
            r = 30
            if male:
                d.ellipse([x - r, y - r, x + r, y + r], fill=c if p in MARK else (190, 190, 190), outline=BLACK, width=3)
                text(x, y, str(p), 30, "white" if p in MARK else BLACK, True, "mm")
            else:
                d.ellipse([x - r, y - r, x + r, y + r], fill="white", outline=c if p in MARK else GREY, width=8 if p in MARK else 3)
                text(x, y, str(p), 30, c if p in MARK else GREY, True, "mm")


text(60, 30, "DB-9: which pin is which (seen from the FRONT, wide row on top)", 44, BLACK, True)
text(60, 92, "The numbers are also moulded in the plastic, very small. Seen from the back (solder side) everything is mirrored.", 26, GREY)

db9(520, 420, True, "MALE (pins)  - your cable's ends", "look at the pins: 1 2 3 4 5 from the LEFT")
db9(1480, 420, False, "FEMALE (holes)  - the MAX3232 board", "look into the holes: 1 2 3 4 5 from the RIGHT")

y = 700
text(60, y, "Legend", 32, BLACK, True)
for i, (p, s) in enumerate(((3, "pin 3 = R1IN on the board: the reader's GREEN (TX) must end up here"),
                            (2, "pin 2 = the board's output (T1OUT): nothing of the reader goes here"),
                            (5, "pin 5 = GND: the reader's BLACK goes here"))):
    c = MARK[p][0]
    d.ellipse([70, y + 60 + i * 52 - 18, 106, y + 60 + i * 52 + 18], fill=c)
    text(125, y + 60 + i * 52, s, 28, c if p != 5 else BLACK, True, "lm")

y = 920
text(60, y, "Bip the cable (multimeter on continuity, cable loose)", 32, BLACK, True)
steps = (
    "1  Tape one end: A = goes into the MAX3232 board.  B = the free end.",
    "2  One probe on A pin 3. Try every pin on B until it beeps:",
    "      B pin 3 beeps  ->  straight cable.     B pin 2 beeps  ->  null-modem (2-3 crossed).",
    "      The pin on B that beeps is where the reader's GREEN goes.",
    "3  One probe on A pin 5, find it on B (almost always B pin 5): the reader's BLACK goes there.",
    "4  B is male too: either cut B off and find the two wire COLOURS that beep to A pin 3 and A pin 5,",
    "      or put a female DB-9 with screw terminals on B.",
    "5  Before anything is connected: reader pin 4 (green) to pin 2 (black) at rest, green on the meter only.",
)
for i, s in enumerate(steps):
    text(80, y + 60 + i * 46, s, 27, BLACK)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print("wrote", os.path.abspath(OUT))
