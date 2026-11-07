import time
import json
import subprocess
import sys
from pathlib import Path


def normalize(text):
    return ("".join(text.split()).upper().replace("-", "").replace(".", "").replace("_", "").replace("·", ""))

assert normalize("7ABC123") == "7ABC123"
assert normalize("7abc123") == "7ABC123"
assert normalize("7-ABC-123") == "7ABC123"
assert normalize("7 ABC 123") == "7ABC123"
assert normalize("京A·12345") == "京A12345"
assert normalize("ROAD WORK AHEAD") == "ROADWORKAHEAD"
assert normalize("7ABC128") != "7ABC123"
    
with open("samples/expected.json", encoding="utf-8") as f:
    expected = json.load(f)

script_dir = Path(__file__).parent


passed = 0
failed = 0

for key, value in expected.items():
    image_path = script_dir / "samples" / key
    output_file = script_dir / "output" / (image_path.stem + "_output.json")

    output_file.unlink(missing_ok=True)

    start = time.perf_counter()
    result = subprocess.run([sys.executable, "app.py", "--input-image", str(image_path)])
    seconds = time.perf_counter() - start

    if result.returncode != 0 or not output_file.exists():
        print(f"FAIL {key} (crash or no output) {seconds:.2f}s")
        failed += 1
        continue
        
    with open(output_file, encoding="utf-8") as f:
        actual = json.load(f)["text"]
    
    if normalize(actual) == normalize(value):
        print(f"PASS {key} {seconds:.2f}s")
        passed += 1
    else:
        print(f"FAIL {key} expected: {value} got: {actual} {seconds:.2f}s")
        failed += 1

print(f"Score: {passed * 20} / {len(expected) *20}")