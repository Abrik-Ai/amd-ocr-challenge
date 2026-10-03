import argparse
import json
from pathlib import Path

from PIL import Image

# Read the image path given on the command line:
#   python3 app.py --input-image input/image_01.png
parser = argparse.ArgumentParser()
parser.add_argument("--input-image")
args = parser.parse_args()
print(f"Input image: {args.input_image}")

# Open the image and report what it is before converting
image = Image.open(args.input_image)
print(f"Format: {image.format}, mode: {image.mode}, size: {image.size}")

# Convert to RGB so every image has three channels, whatever it started as
image = image.convert("RGB")

# Take the file name without folder or extension: input/image_01.png -> image_01
file_name = Path(args.input_image).stem

# The folder this script lives in (/app inside the container)
file_dir = Path(__file__).parent

# Build the output path: <script folder>/output/image_01_output.json
output_path = file_dir / "output" / (file_name + "_output.json")

# Create the output folder if it does not exist yet
output_path.parent.mkdir(exist_ok=True)

# Placeholder answer; the model will produce the real text later
data = {"text": "TEST", "confidence": 0.5}

# Write the answer as JSON
with open(output_path, "w") as f:
    json.dump(data, f)

print(f"Wrote: {output_path}")