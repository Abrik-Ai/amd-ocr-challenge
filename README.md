# Plate and sign OCR on AMD ROCm

My solution to **Mini-Challenge 2 (Optical Character Recognition)** of the AMD AI League on lablab.ai: a Docker container that reads US licence plates, Chinese licence plates and road signs from images, running on AMD GPUs with ROCm.

For each image, the harness runs:

```bash
python3 /app/app.py --input-image /app/input/image_01.png
```

and the container writes `/app/output/image_01_output.json`:

```json
{"text": "7ABC123"}
```

## Results

All numbers measured by me; "MI300X" means the final Docker image on an AMD Instinct MI300X.

| test | score | notes |
|---|---|---|
| 10 official samples, final image, MI300X | **200 / 200** | 0.2–0.4 s per image, healthy after 23 s, peak VRAM 18.0 GiB |
| 10 official samples, AMD Radeon Pro W7900D | 200 / 200 | 0.29–0.58 s per image, peak VRAM 17.2 GiB |
| samples × 10 degradations | 99 / 100 | blur, dark, noise, low contrast, skew, low resolution and 4 combinations |
| synthetic plates and signs, clean | 46 / 46 | 20 US plates, 10 Chinese plates, 16 signs, with texts the model had not seen |
| synthetic × 10 degradations | 454 / 460 | 451 / 460 before the Chinese serial fix (see below) |

Image: built on the mandated `rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0` base, 45.7 GiB uncompressed (limit 60 GiB). PNG, JPEG and TIFF inputs verified.

## How it works

### Model

[Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct), a vision-language model, in bf16 with Hugging Face Transformers, greedy decoding.

I chose a vision-language model over classic OCR (detector + recognizer) because the hard part of this task is the transcription rules, not only reading characters: drop the state name and slogan around a plate number, but keep a Chinese plate's province character. Classic OCR returns every piece of text it finds, so those rules would have to be coded by hand for every plate design. A VLM takes them as instructions.

### Prompt (`prompt.py`)

One prompt encodes the rules: return only the text; for a licence plate, only the registration number; keep a Chinese plate's leading province character and letter; copy characters exactly, without guessing, correcting, or adding units, labels or explanations.

### Post-processing (`ocr.py`)

- Any mix of newlines and spaces becomes single spaces, so multi-line signs come out as `SPEED LIMIT 65`.
- `fix_cn_serial`: on Chinese plates, the 5-character serial never uses the letters I and O (they look like 1 and 0), so any `O`/`I` there is turned into `0`/`1`. Only applied when the text starts with a Chinese character, and never to the province and city code. This fixed 3 failures on the degraded synthetic set and broke none. It is not applied to US plates, where `O` can be legitimate.

### Load once, answer many times (`server.py` + `app.py`)

The harness starts a **new process for every image**, and loading an 8B model takes longer than the 30-second limit per image. So:

```text
container start
  └─ CMD: server.py  ── loads the model once, warms up, listens on 127.0.0.1:8000
                         GET /health   → ready?
                         POST /read    → {"text": ...}

per image (harness):
  python3 /app/app.py --input-image X
     └─ waits for /health, POSTs the path, writes /app/output/<name>_output.json
```

- `server.py` uses only Python's built-in `http.server`, reachable only inside the container. A Docker `HEALTHCHECK` reports the container healthy once the model is loaded.
- `app.py` uses only the standard library and has a **25-second budget** for everything. If the server is not up, crashes or is slow, it still writes valid JSON with an empty answer before the 30-second limit, because one empty answer costs one image, while a timeout scores zero overall.

### Container (`Dockerfile`)

Mandated ROCm base → pinned packages installed with the base's own pip (`/opt/venv/bin/pip`, where ROCm torch lives) → the build fails if pip has replaced ROCm torch with a CUDA build → model weights in `/models` → code in `/app` → `HEALTHCHECK` → `CMD` starts the server. Weights are copied before the code, so code changes rebuild in seconds.

## Testing

The 10 official samples are too few to trust: I tuned the prompt on them, and the graded set is different and harder. So I built two more test sets:

- `degrade.py`: 10 degraded versions of every image (blur, darkness, Gaussian noise, low contrast, 12° rotation, ¼ resolution, and combinations up to rotate + dark + blur + noise). Fixed random seed, so every run produces identical images.
- `synth.py`: draws new plates and signs with Pillow: random US plates (random numbers, states, slogans above or below the number, several colour schemes), Chinese blue plates (all provinces), stop signs, speed limits, advisory plaques and multi-line warning signs. Each image's expected answer is generated together with the drawing.

`score.py` runs `app.py` on a folder of images and scores them with the challenge's normalization (uppercase, whitespace and `- . · _` removed). `check_gates.sh` runs the challenge's pre-submission checklist against the built image on an AMD GPU.

## What did not work

- **Median filter + autocontrast before the model:** 98/100 on the degraded samples, versus 99/100 without it. It fixed nothing and turned a correct `5` into `S` on a blurred plate, so I dropped it.
- **Remaining failures** are almost all on the strongest degradation, which I also found hard to read myself: wrong Chinese province characters (the model falls back to a common one such as 京) and one `7`/`T` confusion. One US plate under heavy noise read `0` as `O`.

## Limitations

- The synthetic images are flat and clean compared with real photos, so passing them is weaker evidence than failing them.
- It is not known whether the harness waits for the health check before the first image. The model loads in about 20–25 s; if the harness starts immediately, the first image still gets answered within its budget, but a slower start would cost one image, not the run.

## Repository

| file | purpose |
|---|---|
| `app.py` | entry point the harness calls; thin client with a 25 s budget and empty-answer fallback |
| `server.py` | loads the model once, answers `/health` and `/read` |
| `ocr.py` | model loading, inference and post-processing |
| `prompt.py` | the transcription prompt |
| `Dockerfile`, `.dockerignore`, `requirements.txt` | the container |
| `check_gates.sh` | pre-submission checks against the built image |
| `score.py` | scores `app.py` on a folder of images |
| `degrade.py`, `synth.py` | harder test sets |
| `make_samples.py` | TODO: describe |
| `notes.md` | experiment log |

To build: download the weights into `models/Qwen3-VL-8B-Instruct` (for example with `hf download Qwen/Qwen3-VL-8B-Instruct --local-dir models/Qwen3-VL-8B-Instruct`), then `docker build -t ocr .` on a machine with Docker. Running it needs an AMD GPU with ROCm (`--device=/dev/kfd --device=/dev/dri`).

## Acknowledgements

Built with AI assistance (Claude) for planning, review and test tooling; the code(mostly), the prompt, design decisions and experiments are my own. Model: Qwen3-VL by the Qwen team. Hardware: AMD Developer Cloud and the AMD hackathon notebooks.