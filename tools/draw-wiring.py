#!/usr/bin/env python3
"""Draws docs/RFID_BRIDGE_WIRING.png: Pegasus PP-30/nR2 -> MAX3232 -> ESP32 DevKit, with LED/buzzer drivers.

Parts: a 30-pin ESP32-WROOM DevKit, a MAX3232 breakout with a female DB-9, one 12 V supply for the reader and,
through a 12->5 V buck, the ESP. The reader's pins (Pegasus PP-30/nR2): 1 = 9-12 V, 2 = GND, 4 = TX (RS-232),
6 = LED contact, 7 = buzzer contact; 3 and 5 not used.
Run: /etc/openhab/.venv/bin/python3 tools/draw-wiring.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "RFID_BRIDGE_WIRING.png")
W, H = 2400, 1960
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f = lambda size, bold=False: ImageFont.truetype(FB if bold else F, size)

RED, GREEN, ORANGE, BLACK, BLUE, GREY, PURPLE, TEAL = (220, 60, 60), (30, 170, 40), (225, 120, 20), (0, 0, 0), (40, 70, 200), (120, 120, 120), (140, 60, 170), (0, 140, 140)
LW = 6


def line(pts, colour, width=LW):
    d.line(pts, fill=colour, width=width, joint="curve")


def dot(x, y, colour=BLACK):
    d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=colour)


def text(x, y, s, size=30, colour=BLACK, bold=False, anchor="la"):
    d.text((x, y), s, font=f(size, bold), fill=colour, anchor=anchor)


def ground(x, y):
    line([(x, y), (x, y + 30)], BLACK)
    for i, w in enumerate((40, 26, 12)):
        d.line([(x - w, y + 30 + i * 12), (x + w, y + 30 + i * 12)], fill=BLACK, width=5)


def box(x0, y0, x1, y1, title, colour=BLACK, sub=None):
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, outline=colour, width=5)
    text((x0 + x1) // 2, y0 + 16, title, 32, colour, True, "ma")
    if sub:
        text((x0 + x1) // 2, y0 + 56, sub, 22, GREY, anchor="ma")


def resistor(x0, x1, y, label, colour):
    """horizontal resistor between x0 and x1 on row y"""
    mid = (x0 + x1) // 2
    line([(x0, y), (mid - 45, y)], colour)
    d.rectangle([mid - 45, y - 18, mid + 45, y + 18], outline=colour, width=5, fill="white")
    line([(mid + 45, y), (x1, y)], colour)
    text(mid, y - 26, label, 24, colour, True, "md")


def vresistor(x, y0, y1, label, colour):
    mid = (y0 + y1) // 2
    line([(x, y0), (x, mid - 40)], colour)
    d.rectangle([x - 16, mid - 40, x + 16, mid + 40], outline=colour, width=5, fill="white")
    line([(x, mid + 40), (x, y1)], colour)
    text(x + 26, mid, label, 24, colour, True, "lm")


def npn(x, yc, colour, name):
    """collector lead ends at (x-60, yc), base at (x, yc+50) going right, emitter lead ends at (x-60, yc+100)"""
    d.ellipse([x - 85, yc - 15, x + 15, yc + 115], outline=GREY, width=4)
    line([(x - 30, yc + 15), (x - 30, yc + 85)], BLACK, 8)              # the bar
    line([(x - 30, yc + 35), (x - 60, yc)], BLACK)                       # collector
    line([(x - 30, yc + 65), (x - 60, yc + 100)], BLACK)                 # emitter
    d.polygon([(x - 60, yc + 100), (x - 52, yc + 80), (x - 72, yc + 88)], fill=BLACK)  # arrow out
    line([(x - 30, yc + 50), (x, yc + 50)], colour)                      # base
    text(x - 100, yc - 12, name, 22, GREY, anchor="rd")


# ---- title ------------------------------------------------------------------------------------------
text(60, 30, "Pegasus PP-30/nR2  ->  MAX3232  ->  ESP32 DevKit (30 pin, WROOM)   \"rfid-serial-bridge\"", 42, bold=True)
text(60, 88, "The reader's RS-232 into the ESP through the MAX3232; the reader's LED and buzzer contacts pulled to GND by "
     "two NPN transistors. One 12 V supply for both.", 25, GREY)

# ---- rows --------------------------------------------------------------------------------------------
V12, VIN, GND_R, V33, RX, LED, BUZ = 230, 520, 610, 700, 830, 1010, 1240

# ---- 12 V supply and the buck -----------------------------------------------------------------------
box(60, 160, 400, 330, "12 V supply", RED, "the reader's own (>= 0.5 A)")
line([(400, V12), (1500, V12)], RED)
text(1000, V12 - 12, "+12 V", 28, RED, True, "md")
line([(400, 300), (460, 300)], BLACK); ground(460, 300)
text(410, 296, "-", 30, BLACK, True, "ld")
text(410, V12 - 6, "+", 30, RED, True, "ld")

box(1500, 160, 1860, 330, "12 -> 5 V buck", ORANGE, "MP1584 / LM2596 / Mini-360")
text(1510, V12 + 26, "IN+", 24, RED, True); text(1850, V12 + 26, "OUT+", 24, ORANGE, True, "ra")
line([(1600, 330), (1600, 360)], BLACK); ground(1600, 360); text(1615, 340, "IN-", 22, GREY)
line([(1760, 330), (1760, 360)], BLACK); ground(1760, 360); text(1775, 340, "OUT-", 22, GREY)
text(1680, 125, "set to 5.0 V with a meter BEFORE the ESP is connected", 24, ORANGE, True, "ma")
line([(1860, V12), (1910, V12), (1910, VIN), (1960, VIN)], ORANGE)
text(1920, 340, "+5 V", 28, ORANGE, True)

# ---- the reader -------------------------------------------------------------------------------------
box(60, 410, 520, 1350, "Pegasus PP-30/nR2", BLACK, "125 kHz EM, RS-232 9600 8N1")
for y, s, c in ((VIN, "1 red     +9..12 V", RED), (GND_R, "2 black   GND", BLACK), (RX, "4 green   TX (RS-232)", GREEN),
                (LED, "6 brown   LED contact", PURPLE), (BUZ, "7 orange  BUZZER", TEAL)):
    text(90, y, s, 30, c, True, "lm")
    dot(520, y, c)
text(90, 1300, "3 white, 5 yellow: not used", 22, GREY, anchor="lm")
dot(620, V12, RED)
line([(620, V12), (620, VIN), (520, VIN)], RED)
line([(520, GND_R), (590, GND_R)], BLACK); ground(590, GND_R)

# ---- MAX3232 board ----------------------------------------------------------------------------------
box(800, 560, 1460, 960, "MAX3232 board", BLUE, "MAX3232 breakout, female DB-9, VCC 3.3 V")
text(820, RX, "DB-9 pin 3  (R1IN)", 22, GREEN, True, "lm")
text(820, 905, "DB-9 pin 5  (GND)", 22, BLACK, True, "lm")
text(1440, V33, "VCC", 22, ORANGE, True, "rm")
text(1440, 765, "GND", 22, BLACK, True, "rm")
text(1440, RX, "RXD  (R1OUT)", 22, BLUE, True, "rm")
text(1440, 905, "TXD - not used", 22, GREY, True, "rm")
line([(520, RX), (800, RX)], GREEN)
text(660, RX - 14, "RS-232", 24, GREEN, True, "md")
line([(800, 905), (740, 905)], BLACK); ground(740, 905)
line([(1460, 765), (1520, 765)], BLACK); ground(1520, 765)

# ---- ESP32 ------------------------------------------------------------------------------------------
box(1960, 410, 2340, 1350, "ESP32 DevKit", BLACK, "30 pin, ESP32-WROOM")
for y, s, c in ((VIN, "VIN", ORANGE), (GND_R, "GND", BLACK), (V33, "3V3", ORANGE), (RX, "RX2  GPIO16", BLUE),
                (LED + 50, "GPIO25", PURPLE), (BUZ + 50, "GPIO26", TEAL)):
    dot(1960, y, c)
    text(1990, y, s, 30, c, True, "lm")
line([(1960, GND_R), (1900, GND_R)], BLACK); ground(1900, GND_R)
line([(1460, V33), (1960, V33)], ORANGE)
text(1710, V33 - 14, "3.3 V  (never 5 V to the MAX3232)", 24, ORANGE, True, "md")
line([(1460, RX), (1960, RX)], BLUE)
text(1710, RX - 14, "TTL 3.3 V", 24, BLUE, True, "md")

# ---- LED and buzzer drivers -------------------------------------------------------------------------
for yc, colour, gpio, name in ((LED, PURPLE, LED + 50, "Q1  NPN  (LED - optional)"), (BUZ, TEAL, BUZ + 50, "Q2  NPN  (buzzer)")):
    x = 1300
    npn(x, yc, colour, name)
    line([(520, yc), (x - 60, yc)], colour)                      # reader contact -> collector
    line([(x - 60, yc + 100), (x - 60, yc + 120)], BLACK); ground(x - 60, yc + 120)
    dot(x + 60, gpio, colour)
    line([(x, gpio), (x + 60, gpio)], colour)
    resistor(x + 60, 1960, gpio, "1 kΩ", colour)
    vresistor(x + 60, gpio, gpio + 110, "10 kΩ", colour)          # base -> emitter (GND): off while the ESP boots
    ground(x + 60, gpio + 110)

# ---- notes ------------------------------------------------------------------------------------------
y = 1480
text(60, y, "Before connecting (reader on its 12 V, nothing else):", 28, BLACK, True)
for i, s in enumerate((
        "pin 4 to pin 2 at rest: negative (-3..-12 V) or about 0 V = RS-232 as expected. About +5 V: stop, ask (then it is TTL).",
        "pin 6 and pin 7 to pin 2: +3..+12 V = pulled up inside, a pull to GND switches them (what Q1/Q2 do). About 0 V: stop, ask.",
        "a short pull of pin 6 to pin 2 through 1 kΩ: the LED changes colour; the same on pin 7: it beeps. Then the transistors.",
        "NPN: BC547 / 2N3904 / 2N2222 (flat side to you: BC547 = C B E, 2N3904 / 2N2222 TO-92 = E B C - check the datasheet).",
        "all GND symbols are one common ground: supply -, reader pin 2, buck IN-/OUT-, MAX3232, ESP, both emitters.",
        "The MAX3232 board's DB-9 is female: a male DB-9 with screw terminals (or solder) takes reader pin 4 on pin 3 and GND on pin 5.",
        "Q1 (LED) is optional - the buzzer alone tells every answer apart; the firmware drives GPIO25 either way (nothing on it is harmless).")):
    text(80, y + 46 + i * 40, "- " + s, 24, BLACK)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print("wrote", os.path.abspath(OUT))
