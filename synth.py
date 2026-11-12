import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"   # path from fc-list

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


def fit_font(d, text, size, max_width, min_size=12):
    """Largest font, starting at `size`, whose text fits in max_width pixels."""
    font = ImageFont.truetype(FONT, size=size)
    while d.textlength(text, font=font) > max_width and size > min_size:
        size -= 2
        font = ImageFont.truetype(FONT, size=size)
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


if __name__ == "__main__":
    rng = random.Random(0)          # fixed seed: same plates every run
    DST.mkdir(exist_ok=True)
    expected = {}
    for i in range(20):
        img, answer = random_us_plate(rng)
        name = f"synth-us-{i:03d}.png"
        img.save(DST / name)
        expected[name] = answer
    json.dump(expected, open(DST / "expected.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"wrote {len(expected)} images to {DST}")