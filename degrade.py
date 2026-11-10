import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).parent
SRC = ROOT / "samples"
DST = ROOT / "samples_hard"
rng = np.random.default_rng(0)   # fixed seed: same "random" images every run


def blur(img):
    return img.filter(ImageFilter.GaussianBlur(radius=3))


def dark(img):
    return ImageEnhance.Brightness(img).enhance(0.25)   # 25% of the original brightness


def noise(img):
    # TODO: add Gaussian noise.
    #   arr = np.asarray(img).astype(np.float32)
    #   add rng.normal(0, 40, arr.shape), clip to 0..255, back to uint8, Image.fromarray(...)
    arr = np.asarray(img).astype(np.float32)
    arr += rng.normal(0, 40, arr.shape)
    arr = np.clip(arr, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))
   

def low_contrast(img):
    # TODO: like dark(), but with ImageEnhance.Contrast and a factor around 0.3
    return ImageEnhance.Contrast(img).enhance(0.3)


def skew(img):
    # TODO: rotate by 12 degrees, expand=True so corners aren't cut,
    #   fillcolor=(128, 128, 128) so the new corners are grey, not black
    return img.rotate(12, expand=True, fillcolor=(128, 128, 128))


def tiny(img):
    # TODO: shrink to 1/4 width and height with img.resize(...), then back to the original size.
    #   It simulates a far-away camera: the pixels get blocky.
    small = img.resize((img.width // 4, img.height // 4))
    return small.resize((img.width, img.height), Image.Resampling.NEAREST)


def dark_blur(img):
    return blur(dark(img))          # done as the example


def skew_noise(img):
    # TODO: skew first, then noise
    return noise(skew(img))


def tiny_lowcontrast(img):
    # TODO: tiny first, then low contrast
    return low_contrast(tiny((img)))


def worst(img):
    # TODO: chain FOUR transforms: skew, dark, blur, noise (in that order)
    return noise(blur(dark(skew(img))))

TRANSFORMS = {"blur": blur, "dark": dark, "noise": noise,
              "lowcontrast": low_contrast, "skew": skew, "tiny": tiny,
              "darkblur": dark_blur, "skewnoise": skew_noise,
              "tinylowcontrast": tiny_lowcontrast, "worst": worst}

expected = json.load(open(SRC / "expected.json", encoding="utf-8"))
DST.mkdir(exist_ok=True)
hard = {}

for name, answer in expected.items():
    img = Image.open(SRC / name).convert("RGB")
    stem = Path(name).stem
    for t_name, fn in TRANSFORMS.items():
        out_name = f"{stem}_{t_name}.png"
        fn(img).save(DST / out_name)
        hard[out_name] = answer

json.dump(hard, open(DST / "expected.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"wrote {len(hard)} images to {DST}")