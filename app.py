import argparse
import json
import time
import urllib.request
from pathlib import Path

SERVER = "http://127.0.0.1:8000"
BUDGET = 25.0          # seconds for everything; the hard limit is 30, so keep 5 s spare


def write_output(input_path, text):
    file_name = Path(input_path).stem
    file_dir = Path(__file__).parent

    output_path = file_dir / "output" / (file_name + "_output.json")
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"text": text}, f, ensure_ascii=False)


def wait_for_server(deadline):
    """Poll /health until the server answers or the deadline passes."""
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"{SERVER}/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def read_text(image_path, deadline):
    """Ask the server; return "" on any failure, never raise."""
    try:
        if not wait_for_server(deadline):
            return ""
        req = urllib.request.Request(
            f"{SERVER}/read",
            data=json.dumps({"path": str(Path(image_path).resolve())}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        remaining = max(1.0, deadline - time.monotonic())
        with urllib.request.urlopen(req, timeout=remaining) as r:
            return json.loads(r.read().decode("utf-8")).get("text", "")
    except Exception:
        return ""


def main():
    deadline = time.monotonic() + BUDGET
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-image", required=True)
    args = parser.parse_args()

    text = read_text(args.input_image, deadline)
    write_output(args.input_image, text)


if __name__ == "__main__":
    main()