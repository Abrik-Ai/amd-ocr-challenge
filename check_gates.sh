#!/usr/bin/env bash
# Pre-submission gate checks, run on the AMD cloud VM after `docker build`.
# Usage: ./check_gates.sh <image:tag> [samples_dir]
# Mirrors the PDF's "Check your submission before you send it" list.
set -u

IMAGE="${1:?usage: ./check_gates.sh <image:tag> [samples_dir]}"
SAMPLES="${2:-samples}"
BASE="rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0"
NAME="ocr-gatecheck"
FAIL=0
pass() { echo "  PASS  $*"; }
fail() { echo "  FAIL  $*"; FAIL=1; }

echo "== 1. base image and size"
base_layers=$(docker image inspect --format '{{json .RootFS.Layers}}' "$BASE")
img_layers=$(docker image inspect --format '{{json .RootFS.Layers}}' "$IMAGE")
python3 - "$base_layers" "$img_layers" <<'EOF' && pass "lower layers match the mandated base" || fail "image is NOT built on the mandated base (or was squashed)"
import json, sys
base, img = json.loads(sys.argv[1]), json.loads(sys.argv[2])
sys.exit(0 if img[:len(base)] == base else 1)
EOF
bytes=$(docker image inspect --format '{{.Size}}' "$IMAGE")
gib=$(python3 -c "print(f'{$bytes / 2**30:.1f}')")
python3 -c "import sys; sys.exit(0 if $bytes < 60 * 2**30 else 1)" \
    && pass "uncompressed size ${gib} GiB (limit 60)" || fail "size ${gib} GiB is over 60 GiB"
docker history --no-trunc --format '{{.Size}}\t{{.CreatedBy}}' "$IMAGE" | head -n 8

echo "== 2. contents (paths, python, no secrets)"
docker run --rm --entrypoint sh "$IMAGE" -c '
  for f in /app/app.py /app/server.py /app/ocr.py /app/prompt.py /app/requirements.txt; do
    test -f "$f" && echo "  PASS  $f" || echo "  FAIL  $f missing"; done
  test -d /models && echo "  PASS  /models exists ($(du -sh /models | cut -f1))" || echo "  FAIL  /models missing"
  echo "  INFO  python3 -> $(command -v python3)"
  python3 -c "import torch, transformers; print(\"  INFO  torch\", torch.__version__, \"| transformers\", transformers.__version__)"
  found=$(find / -xdev \( -name ".env" -o -name "*.pem" -o -name "id_rsa*" \) 2>/dev/null | head -n 5)
  test -z "$found" && echo "  PASS  no .env / key files found" || echo "  FAIL  possible secrets: $found"
' | tee /tmp/gate_contents.txt
grep -q "FAIL" /tmp/gate_contents.txt && FAIL=1

echo "== 3. startup (until HEALTHCHECK says healthy; limit 10 min)"
docker rm -f "$NAME" >/dev/null 2>&1
( while true; do amd-smi metric --mem 2>/dev/null | grep -i used_vram; sleep 1; done ) > /tmp/gate_vram.log 2>&1 &
VRAM_PID=$!
start=$(date +%s)
docker run -d --name "$NAME" --device=/dev/kfd --device=/dev/dri --group-add video \
    --security-opt seccomp=unconfined --ipc=host "$IMAGE" >/dev/null
status="starting"
while [ "$status" != "healthy" ]; do
    sleep 2
    status=$(docker inspect --format '{{.State.Health.Status}}' "$NAME" 2>/dev/null || echo "gone")
    running=$(docker inspect --format '{{.State.Running}}' "$NAME" 2>/dev/null || echo false)
    if [ "$running" != "true" ] || [ "$status" = "unhealthy" ] || [ $(( $(date +%s) - start )) -gt 600 ]; then
        fail "container did not become healthy (status=$status, running=$running)"; docker logs --tail 30 "$NAME"
        kill "$VRAM_PID"; docker rm -f "$NAME" >/dev/null; echo; echo "RESULT: FAIL"; exit 1
    fi
done
pass "healthy after $(( $(date +%s) - start )) s (limit 600)"

echo "== 4. every sample via app.py: time per image, output file, answer"
docker exec "$NAME" mkdir -p /app/input
docker cp "$SAMPLES/." "$NAME:/app/input/" >/dev/null
total_start=$(date +%s)
python3 - "$NAME" "$SAMPLES/expected.json" <<'EOF' || FAIL=1
import json, subprocess, sys, time
name, exp_path = sys.argv[1], sys.argv[2]
expected = json.load(open(exp_path, encoding="utf-8"))
norm = lambda t: "".join(t.split()).upper().replace("-", "").replace(".", "").replace("_", "").replace("·", "")
ok, bad = 0, 0
for img, answer in expected.items():
    stem = img.rsplit(".", 1)[0]
    t0 = time.perf_counter()
    r = subprocess.run(["docker", "exec", name, "python3", "/app/app.py", "--input-image", f"/app/input/{img}"])
    dt = time.perf_counter() - t0
    out = subprocess.run(["docker", "exec", name, "cat", f"/app/output/{stem}_output.json"], capture_output=True)
    try:
        data = json.loads(out.stdout.decode("utf-8"))
        text = data["text"]
        assert isinstance(text, str)
    except Exception:
        print(f"  FAIL  {img}: missing or malformed output JSON ({dt:.2f}s)"); bad += 1; continue
    good_time = dt < 30
    match = norm(text) == norm(answer)
    tag = "PASS " if (match and good_time and r.returncode == 0) else "FAIL "
    print(f"  {tag} {img:18} {dt:5.2f}s  got {text!r}" + ("" if match else f"  expected {answer!r}"))
    ok, bad = ok + (tag == "PASS "), bad + (tag != "PASS ")
print(f"  INFO  {ok}/{ok + bad} correct = {ok * 20}/{(ok + bad) * 20} points")
sys.exit(1 if bad else 0)
EOF
total=$(( $(date +%s) - total_start ))
[ "$total" -lt 600 ] && pass "all samples in ${total} s (limit 600)" || fail "total run ${total} s is over 600 s"

echo "== 5. VRAM peak (limit 1-48 GiB)"
kill "$VRAM_PID" 2>/dev/null
python3 - /tmp/gate_vram.log <<'EOF' || FAIL=1
import re, sys
vals = [int(v) for v in re.findall(r"USED_VRAM: (\d+)", open(sys.argv[1], errors="ignore").read())]
if not vals:
    print("  FAIL  no VRAM readings (is amd-smi available on this host?)"); sys.exit(1)
peak = max(vals) / 1024
ok = 1 <= peak <= 48 * 1.01
print(f"  {'PASS' if ok else 'FAIL'}  peak {peak:.1f} GiB over {len(vals)} readings")
sys.exit(0 if ok else 1)
EOF

docker rm -f "$NAME" >/dev/null
echo
[ "$FAIL" -eq 0 ] && echo "RESULT: ALL GATES PASS" || echo "RESULT: FAIL (see above)"
exit "$FAIL"