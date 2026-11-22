#!/usr/bin/env python3
"""Draws docs/OVERVIEW.png: the whole path of one reading - tag -> reader -> MAX3232 -> ESP32 -> MQTT -> openHAB -> the
answer back to the reader's buzzer/LED - and the frame on the wire with its checksum (an invented tag).
Run: /etc/openhab/.venv/bin/python3 tools/draw-overview.py"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "OVERVIEW.png")
W, H = 2680, 1330
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
f = lambda s, b=False: ImageFont.truetype(FB if b else F, s)
fm = lambda s: ImageFont.truetype(FM, s)
INK, GREY, LIGHT = (25, 30, 40), (120, 125, 135), (244, 246, 250)
GREEN, BLUE, ORANGE, PURPLE, RED, TEAL = (30, 150, 60), (40, 90, 200), (220, 120, 20), (130, 70, 180), (200, 50, 50), (0, 140, 140)


def text(x, y, s, size=28, c=INK, b=False, a="la", font=None):
    d.text((x, y), s, font=font or f(size, b), fill=c, anchor=a)


def card(x, y, w, h, title, lines, colour):
    d.rounded_rectangle([x + 6, y + 8, x + w + 6, y + h + 8], radius=22, fill=(225, 228, 235))
    d.rounded_rectangle([x, y, x + w, y + h], radius=22, fill="white", outline=colour, width=5)
    d.rounded_rectangle([x, y, x + w, y + 62], radius=22, fill=colour)
    d.rectangle([x, y + 40, x + w, y + 62], fill=colour)
    text(x + w // 2, y + 31, title, 30, "white", True, "mm")
    for i, s in enumerate(lines):
        text(x + 22, y + 92 + i * 38, s, 24, INK if not s.startswith("·") else GREY)


def arrow(x0, y0, x1, y1, colour, label=None, above=True, width=7):
    d.line([(x0, y0), (x1, y1)], fill=colour, width=width)
    import math
    a = math.atan2(y1 - y0, x1 - x0)
    p = [(x1, y1), (x1 - 26 * math.cos(a) + 13 * math.sin(a), y1 - 26 * math.sin(a) - 13 * math.cos(a)),
         (x1 - 26 * math.cos(a) - 13 * math.sin(a), y1 - 26 * math.sin(a) + 13 * math.cos(a))]
    d.polygon(p, fill=colour)
    if label:
        text((x0 + x1) // 2, (y0 + y1) // 2 + (-16 if above else 16), label, 22, colour, True, "md" if above else "ma")


# ---- title -------------------------------------------------------------------------------------
text(70, 50, "rfid-rs232-esp32-mqtt", 54, INK, True)
text(70, 118, "One reading, from the tag to the decision and back to the door. The bridge checks and forwards; it never decides.", 28, GREY)

# ---- the chain ---------------------------------------------------------------------------------
GAP = 150
WS = [300, 360, 330, 420, 520]
XS = [70]
for w in WS[:-1]:
    XS.append(XS[-1] + w + GAP)
Y, CH = 230, 300
card(XS[0], Y, WS[0], CH, "Tag", ["EM4100, 125 kHz", "card, fob or", "any EM4100 tag", "· read-only, 40-bit ID"], GREY)
card(XS[1], Y, WS[1], CH, "RFID reader", ["Pegasus PP-30/nR2", "(or any EM reader with", "RS-232 ASCII out)", "· 9600 8N1, 9-12 V"], INK)
card(XS[2], Y, WS[2], CH, "MAX3232", ["RS-232 ±V levels", "-> 3.3 V TTL", "VCC from the ESP's 3V3", "· R1IN = DB-9 pin 3"], BLUE)
card(XS[3], Y, WS[3], CH, "ESP32 (ESPHome)", ["frame: exactly 12 hex", "+ EM4100 XOR checksum", "debounce: held tag = once", "· counts ok / bad / lost"], GREEN)
card(XS[4], Y, WS[4], CH, "MQTT -> openHAB", ["TLS on 8883, QoS 1", "<base>/tag - not retained", "-> a trigger channel (no state)", "· a rule looks the tag up"], PURPLE)
for i, (lab, col) in enumerate((("125 kHz", GREY), ("RS-232", INK), ("UART2", BLUE), ("WiFi", GREEN))):
    arrow(XS[i] + WS[i] + 12, Y + 150, XS[i + 1] - 12, Y + 150, col, lab)

# ---- the answer back ---------------------------------------------------------------------------
YB = Y + CH + 120
card(XS[4], YB, WS[4], 270, "The decision", ["known tag -> arm / disarm", "unknown tag -> SMS", "answer on <base>/feedback", "· one rule writes it"], PURPLE)
card(XS[3], YB, WS[3], 270, "ESP32: the answer", ["only within 10 s of its", "own reading - a stray", "message never beeps", "· GPIO26 buzzer, GPIO25 LED"], GREEN)
DW = XS[3] - GAP - XS[1]
card(XS[1], YB, DW, 270, "At the door", ["arm      ->  two short beeps  (+ LED 2 s)", "disarm   ->  one short beep   (+ LED 2 s)",
                                          "denied   ->  three long beeps", "no MQTT  ->  three long beeps: nothing happened"], TEAL)
text(XS[1] + DW - 20, YB + 92, "NPN to GND on the", 22, GREY, a="ra")
text(XS[1] + DW - 20, YB + 122, "reader's contacts", 22, GREY, a="ra")
arrow(XS[4] - 12, YB + 150, XS[3] + WS[3] + 12, YB + 150, PURPLE, "answer")
arrow(XS[3] - 12, YB + 150, XS[1] + DW + 12, YB + 150, GREEN, "NPN")
mid = XS[4] + WS[4] // 2
arrow(mid, Y + CH + 12, mid, YB - 12, PURPLE)

# ---- the frame on the wire ---------------------------------------------------------------------
YF = YB + 270 + 90
text(70, YF, "The frame on the wire (an invented tag)", 32, INK, True)
cells = [("STX", "02", GREY)] + [(c, "", BLUE) for c in "123456789A"] + [(c, "", ORANGE) for c in "92"] + \
        [("CR", "0D", GREY), ("LF", "0A", GREY), ("ETX", "03", GREY)]
x = 70
for label, hexv, colour in cells:
    w = 96 if len(label) > 1 else 74
    d.rounded_rectangle([x, YF + 60, x + w, YF + 150], radius=10, fill=LIGHT, outline=colour, width=4)
    text(x + w // 2, YF + 105, label, 34 if len(label) == 1 else 26, colour, True, "mm", fm(34 if len(label) == 1 else 24))
    if hexv:
        text(x + w // 2, YF + 172, "0x" + hexv, 20, GREY, a="ma")
    x += w + 10
text(x + 30, YF + 70, "10 digits = the tag's 5 bytes   12 34 56 78 9A", 26, BLUE, True)
text(x + 30, YF + 112, "2 digits = their XOR   12^34^56^78^9A = 92", 26, ORANGE, True)
text(x + 30, YF + 154, "anything else -> a bad frame, counted, never sent", 26, RED, True)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print("wrote", os.path.abspath(OUT))
