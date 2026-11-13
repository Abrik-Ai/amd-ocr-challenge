import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# Usage:
#   python degrade.py                                  -> samples/       -> samples_hard/
#   python degrade.py samples_synth samples_synth_hard -> any source     -> any destination
ROOT = Path(__file__).parent
SRC = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "samples")
DST = ROOT / (sys.argv[2] if len(sys.argv) > 2 else "samples_hard")
rng = np.random.default_rng(0)   # fixed seed: same "random" images every run


def blur(img):
    return img.filter(ImageFilter.GaussianBlur(radius=3))


def dark(img):
    return ImageEnhance.Brightness(img).enhance(0.25)   # 25% of the original brightness


def noise(img):
    arr = np.asarray(img).astype(np.float32)
    arr += rng.normal(0, 40, arr.shape)
    arr = np.clip(arr, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def low_contrast(img):
    return ImageEnhance.Contrast(img).enhance(0.3)


def skew(img):
    return img.rotate(12, expand=True, fillcolor=(128, 128, 128))


def tiny(img):
    small = img.resize((img.width // 4, img.height // 4))
    return small.resize((img.width, img.height), Image.Resampling.NEAREST)


def dark_blur(img):
    return blur(dark(img))


def skew_noise(img):
    return noise(skew(img))


def tiny_lowcontrast(img):
    return low_contrast(tiny(img))


def worst(img):
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
print(f"wrote {len(hard)} images from {SRC.name}/ to {DST.name}/")