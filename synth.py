from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"   # path from fc-list

PLATE_WHITE = (245, 245, 240)
NUMBER_BLUE = (30, 40, 110)
STATE_RED = (190, 40, 40)
SLOGAN_GREY = (60, 60, 60)


def fit_font(d, text, size, max_width, min_size=12):
    """Largest font, starting at `size`, whose text fits in max_width pixels."""
    font = ImageFont.truetype(FONT, size=size)
    while d.textlength(text, font=font) > max_width and size > min_size:
        size -= 2
        font = ImageFont.truetype(FONT, size=size)
    return font


def us_plate(number, state, slogan, slogan_on_top=False):
    W, H = 600, 300
    M = 40                                   # margin: grey background around the plate
    img = Image.new("RGB", (W + 2 * M, H + 2 * M), (95, 95, 100))
    d = ImageDraw.Draw(img)

    # 1. the plate: white, rounded corners, thin dark border
    d.rounded_rectangle((M, M, M + W, M + H), radius=25,
                        fill=PLATE_WHITE, outline=(40, 40, 40), width=4)

    # 2. the number: big, dark blue, centred; shrinks to fit 90% of the plate's width
    cx, cy = M + W // 2, M + H // 2
    d.text((cx, cy), number, font=fit_font(d, number, 140, 0.9 * W),
           fill=NUMBER_BLUE, anchor="mm")

    # 3. state near the top edge, slogan near the bottom edge (swapped if slogan_on_top)
    top_y, bottom_y = M + 45, M + H - 45
    state_y, slogan_y = (bottom_y, top_y) if slogan_on_top else (top_y, bottom_y)
    d.text((cx, state_y), state, font=fit_font(d, state, 40, 0.9 * W),
           fill=STATE_RED, anchor="mm")
    d.text((cx, slogan_y), slogan, font=fit_font(d, slogan, 40, 0.9 * W),
           fill=SLOGAN_GREY, anchor="mm")

    return img


if __name__ == "__main__":
    us_plate("4KXM218", "TEXAS", "THE LONE STAR STATE").save("synth_test.png")
    us_plate("4KXM218", "TEXAS", "THE LONE STAR STATE", slogan_on_top=True).save("synth_test_swapped.png")
    print("saved synth_test.png and synth_test_swapped.png")