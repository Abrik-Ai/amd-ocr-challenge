import torch
from PIL import Image
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

from prompt import PROMPT

MODEL_DIR = "/models/Qwen3-VL-8B-Instruct"   # path inside the container; Colab passes its own


def load(model_dir=MODEL_DIR):
    """Load model + processor once. Slow (~45 s cold)."""
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        model_dir, dtype=torch.bfloat16, device_map="cuda")
    processor = AutoProcessor.from_pretrained(model_dir)
    return model, processor


def fix_cn_serial(text):
    """Chinese plates: the 5-char serial after the first two characters never contains I or O."""
    if text and "\u4e00" <= text[0] <= "\u9fff":
        head, tail = text[:2], text[2:]
        return head + tail.replace("O", "0").replace("I", "1")
    return text


def read(model, processor, image_path):
    """One image path in, cleaned text out. Fast (~1 s)."""
    image = Image.open(image_path).convert("RGB")   # PNG, JPEG and TIFF all open the same way
    messages = [{"role": "user", "content": [
        {"type": "image", "image": image},
        {"type": "text", "text": PROMPT},
    ]}]
    inputs = processor.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                           return_dict=True, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, do_sample=False, max_new_tokens=32)
    text = processor.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]

    text = " ".join(text.split())   # any mix of newlines/spaces -> single spaces
    text = fix_cn_serial(text)      # Chinese plates: O -> 0, I -> 1 in the serial
    return text