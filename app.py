import argparse
import json
from pathlib import Path

from PIL import Image


def load_image(path):
    image = Image.open(path).convert("RGB")
    return image

def write_output(input_path, text, confidence):
    file_name = Path(input_path).stem
    file_dir = Path(__file__).parent

    output_path = file_dir / "output" / (file_name + "_output.json")
    output_path.parent.mkdir(exist_ok=True)

    data = {"text": text, "confidence": confidence}
    
    with open(output_path, "w", encoding="utf-8") as f :
        json.dump(data, f)

def read_text(image):
    return "TEST", 0.5

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-image", required=True)
    args = parser.parse_args()

    image = load_image(args.input_image)
    text, confidence = read_text(image)
    write_output(args.input_image, text, confidence)


if __name__ == "__main__":
    main()
