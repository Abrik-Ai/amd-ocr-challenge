import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"   # path from fc-list
# Chinese font: a .ttc file holds several fonts; index 2 = Simplified Chinese (SC).
# Check yours with: fc-list -f '%{file} | %{index} | %{family[0]}\n' | grep -i NotoSansCJK-Bold
CJK_FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
CJK_INDEX = 2

ROOT = Path(__file__).parent
DST = ROOT / "samples_synth"

# --- pools to draw random plates from -----------------------------------------
STATES = ["TEXAS", "NEW YORK", "CALIFORNIA", "FLORIDA", "ILLINOIS", "OHIO",
          "MICHIGAN", "LOUISIANA", "MAINE", "NEW JERSEY", "OREGON", "ARIZONA"]
SLOGANS = ["THE LONE STAR STATE", "EXCELSIOR", "SUNSHINE STATE", "LAND OF LINCOLN",
           "GARDEN STATE", "VACATIONLAND", "LIVE FREE OR DIE", "PURE MICHIGAN",
           "SPORTSMANS PARADISE", "GRAND CANYON STATE", "BIRTHPLACE OF AVIATION"]
# number patterns: L = letter, D = digit; "-" and " " are drawn as-is
PATTERNS = ["DLLL DDD", "LLL DDDD", "LLL-DDDD", "DLLLDDD", "LLLDDD", "DDD LLL", "LLDDLLL"]
LETTERS = "ABCDEFGHJKLMNPRSTUVWXYZ"   # no I, O, Q: most US states skip them (look like 1, 0)

# (plate, number, state, slogan) colour schemes
SCHEMES = [
    ((245, 245, 240), (30, 40, 110), (190, 40, 40), (60, 60, 60)),    # white, blue number
    ((250, 250, 250), (20, 20, 20), (20, 60, 140), (80, 80, 80)),     # white, black number
    ((245, 235, 180), (25, 25, 25), (120, 30, 30), (60, 60, 60)),     # pale yellow
    ((235, 245, 235), (20, 90, 40), (20, 90, 40), (50, 50, 50)),      # green number
]


def fit_font(d, text, size, max_width, min_size=12, path=FONT, index=0):
    """Largest font, starting at `size`, whose text fits in max_width pixels."""
    font = ImageFont.truetype(path, size=size, index=index)
    while d.textlength(text, font=font) > max_width and size > min_size:
        size -= 2
        font = ImageFont.truetype(path, size=size, index=index)
    return font


def us_plate(number, state, slogan, slogan_on_top=False, colors=SCHEMES[0]):
    plate_c, number_c, state_c, slogan_c = colors
    W, H = 600, 300
    M = 40                                   # margin: grey background around the plate
    img = Image.new("RGB", (W + 2 * M, H + 2 * M), (95, 95, 100))
    d = ImageDraw.Draw(img)

    # 1. the plate: rounded corners, thin dark border
    d.rounded_rectangle((M, M, M + W, M + H), radius=25,
                        fill=plate_c, outline=(40, 40, 40), width=4)

    # 2. the number: big, centred; shrinks to fit 90% of the plate's width
    cx, cy = M + W // 2, M + H // 2
    d.text((cx, cy), number, font=fit_font(d, number, 140, 0.9 * W),
           fill=number_c, anchor="mm")

    # 3. state near the top edge, slogan near the bottom edge (swapped if slogan_on_top)
    top_y, bottom_y = M + 45, M + H - 45
    state_y, slogan_y = (bottom_y, top_y) if slogan_on_top else (top_y, bottom_y)
    d.text((cx, state_y), state, font=fit_font(d, state, 40, 0.9 * W),
           fill=state_c, anchor="mm")
    d.text((cx, slogan_y), slogan, font=fit_font(d, slogan, 40, 0.9 * W),
           fill=slogan_c, anchor="mm")

    return img


def random_number(rng):
    pattern = rng.choice(PATTERNS)
    return "".join(rng.choice(LETTERS) if c == "L" else
                   str(rng.randint(0, 9)) if c == "D" else c
                   for c in pattern)


def random_us_plate(rng):
    """One random plate and its expected answer (the number only)."""
    number = random_number(rng)
    img = us_plate(number,
                   state=rng.choice(STATES),
                   slogan=rng.choice(SLOGANS),
                   slogan_on_top=rng.random() < 0.5,
                   colors=rng.choice(SCHEMES))
    return img, number


# --- Chinese plates -------------------------------------------------------------
# Province abbreviations (one character each): the first character of every plate
PROVINCES = "京津沪渝冀晋辽吉黑苏浙皖闽赣鲁豫鄂湘粤桂琼川贵云陕甘青宁新藏蒙"
CN_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"   # no I, O on Chinese plates
CN_BLUE = (20, 70, 170)


def cn_plate(text):
    """Standard blue Chinese plate: white characters, white inner border."""
    W, H = 600, 190                          # real plates are ~440 x 140 mm, about 3:1
    M = 40
    img = Image.new("RGB", (W + 2 * M, H + 2 * M), (95, 95, 100))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle((M, M, M + W, M + H), radius=14, fill=CN_BLUE)
    d.rounded_rectangle((M + 8, M + 8, M + W - 8, M + H - 8), radius=10,
                        outline=(240, 240, 240), width=4)

    font = fit_font(d, text, 130, 0.88 * W, path=CJK_FONT, index=CJK_INDEX)
    d.text((M + W // 2, M + H // 2), text, font=font, fill=(245, 245, 245), anchor="mm")
    return img


def random_cn_plate(rng):
    """One random blue plate: province + city letter + '·' + 5 characters."""
    serial = "".join(rng.choice(CN_LETTERS) if rng.random() < 0.25 else str(rng.randint(0, 9))
                     for _ in range(5))
    text = f"{rng.choice(PROVINCES)}{rng.choice(CN_LETTERS)}·{serial}"
    return cn_plate(text), text


# --- Road signs -----------------------------------------------------------------
BLACK, WHITE = (20, 20, 20), (245, 245, 245)
STOP_RED, WARN_YELLOW, WORK_ORANGE = (190, 30, 35), (245, 200, 30), (240, 120, 30)
SKIES = [(150, 185, 215), (190, 205, 215), (120, 150, 110), (170, 170, 165)]   # backgrounds

# work zone signs are orange, other warnings yellow; each entry is the sign's lines
WORK_SIGNS = [["ROAD", "WORK", "AHEAD"], ["RIGHT", "LANE", "CLOSED"], ["DETOUR", "AHEAD"],
              ["FLAGGER", "AHEAD"], ["END", "ROAD WORK"], ["SHOULDER", "CLOSED"],
              ["ONE LANE", "ROAD", "AHEAD"]]
WARN_SIGNS = [["ICY", "BRIDGE"], ["BRIDGE", "ICES BEFORE", "ROAD"], ["LOOSE", "GRAVEL"],
              ["FALLING", "ROCKS"], ["NARROW", "BRIDGE"], ["SLOW", "TRAFFIC", "AHEAD"]]


def sign_canvas(rng, S=560):
    """Square background with a pole; the sign is drawn on top of it."""
    img = Image.new("RGB", (S, S), rng.choice(SKIES))
    d = ImageDraw.Draw(img)
    d.rectangle((S // 2 - 12, S // 2, S // 2 + 12, S), fill=(110, 110, 115))   # pole
    return img, d, S


def draw_lines(d, lines, cx, cy, max_width, line_h, color):
    """Stacked lines centred around (cx, cy); one font size for all, fitted to the widest."""
    widest = max(lines, key=len)
    font = fit_font(d, widest, int(line_h * 0.85), max_width)
    top = cy - line_h * (len(lines) - 1) / 2
    for k, line in enumerate(lines):
        d.text((cx, top + k * line_h), line, font=font, fill=color, anchor="mm")


def stop_sign(rng):
    img, d, S = sign_canvas(rng)
    c, r = S / 2, S * 0.42
    pts = [(c + r * math.cos(math.radians(22.5 + 45 * k)),
            c + r * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    d.polygon(pts, fill=WHITE)
    inner = [(c + (x - c) * 0.92, c + (y - c) * 0.92) for x, y in pts]
    d.polygon(inner, fill=STOP_RED)
    draw_lines(d, ["STOP"], c, c, 0.62 * S, 0.30 * S, WHITE)
    return img, "STOP"


def speed_limit_sign(rng):
    img, d, S = sign_canvas(rng)
    speed = rng.randrange(15, 80, 5)
    box = (S * 0.22, S * 0.08, S * 0.78, S * 0.82)
    d.rounded_rectangle(box, radius=18, fill=WHITE, outline=BLACK, width=7)
    w = box[2] - box[0]
    draw_lines(d, ["SPEED", "LIMIT"], S / 2, S * 0.27, 0.8 * w, 0.13 * S, BLACK)
    draw_lines(d, [str(speed)], S / 2, S * 0.60, 0.8 * w, 0.32 * S, BLACK)
    return img, f"SPEED LIMIT {speed}"


def advisory_plaque(rng):
    """Yellow square plaque with a number and no words (the challenge's convention)."""
    img, d, S = sign_canvas(rng)
    speed = rng.randrange(15, 60, 5)
    box = (S * 0.22, S * 0.15, S * 0.78, S * 0.71)
    d.rounded_rectangle(box, radius=16, fill=WARN_YELLOW, outline=BLACK, width=7)
    draw_lines(d, [str(speed)], S / 2, (box[1] + box[3]) / 2, 0.42 * S, 0.40 * S, BLACK)
    return img, str(speed)


def warning_sign(rng):
    """Diamond with 1-3 lines of text; orange for work zone signs, yellow otherwise."""
    img, d, S = sign_canvas(rng)
    work = rng.random() < 0.5
    lines = rng.choice(WORK_SIGNS if work else WARN_SIGNS)
    c, r = S / 2, S * 0.46
    d.polygon([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], fill=BLACK)
    r2 = r * 0.94
    d.polygon([(c, c - r2), (c + r2, c), (c, c + r2), (c - r2, c)],
              fill=WORK_ORANGE if work else WARN_YELLOW)
    # text must fit inside the diamond: narrower block the more lines there are
    line_h = S * (0.13 if len(lines) == 3 else 0.17)
    draw_lines(d, lines, c, c, S * (0.44 if len(lines) == 3 else 0.58), line_h, BLACK)
    return img, " ".join(lines)


SIGN_MAKERS = [(stop_sign, 3), (speed_limit_sign, 4), (advisory_plaque, 3), (warning_sign, 6)]


if __name__ == "__main__":
    rng = random.Random(0)          # fixed seed: same plates every run
    DST.mkdir(exist_ok=True)
    expected = {}
    for i in range(20):
        img, answer = random_us_plate(rng)
        name = f"synth-us-{i:03d}.png"
        img.save(DST / name)
        expected[name] = answer
    for i in range(10):
        img, answer = random_cn_plate(rng)
        name = f"synth-cn-{i:03d}.png"
        img.save(DST / name)
        expected[name] = answer
    i = 0
    for maker, count in SIGN_MAKERS:
        for _ in range(count):
            img, answer = maker(rng)
            name = f"synth-sign-{i:03d}.png"
            img.save(DST / name)
            expected[name] = answer
            i += 1
    json.dump(expected, open(DST / "expected.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"wrote {len(expected)} images to {DST}")