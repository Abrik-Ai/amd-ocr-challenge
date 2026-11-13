import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import ocr

HOST, PORT = "127.0.0.1", 8000          # only reachable from inside the container
MODEL_DIR = os.environ.get("MODEL_DIR", ocr.MODEL_DIR)

print(f"loading model from {MODEL_DIR} ...", flush=True)
# TODO 1: load the model ONCE, here at module level, with ocr.load(...)
model, processor = ocr.load(MODEL_DIR)

# warm-up: one inference on a blank image, so the first real image is fast
from PIL import Image
Image.new("RGB", (64, 64), "white").save("/tmp/warmup.png")
ocr.read(model, processor, "/tmp/warmup.png")
print("model loaded, warmed up, serving", flush=True)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok"})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/read":
            self.send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers["Content-Length"])
            # TODO 2: read `length` bytes from self.rfile, decode them, json.loads -> request dict
            request = self.rfile.read(length).decode("utf-8")
            request = json.loads(request)
            # TODO 3: call ocr.read with the model, processor and request["path"]
            text = ocr.read(model, processor, request["path"])
            self.send_json(200, {"text": text})
        except Exception as e:                       # bad image, bad request, ...: answer, don't crash
            self.send_json(500, {"error": f"{type(e).__name__}: {e} "})


if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()