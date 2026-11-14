# Experiment notes: OCR challenge

## Results (Qwen3-VL-8B-Instruct, bf16, Colab L4, prompt v1)

| set | images | score |
|---|---|---|
| samples, degraded x10 | 100 | 99/100 |
| synthetic clean (20 US, 10 CN, 16 signs) | 46 | 46/46 |
| synthetic degraded x10 | 460 | 454/460 (before CN fix: 451/460) |

- fix_cn_serial: Chinese plate serials never use I/O -> O to 0, I to 1 after the first two characters. Fixed 3 failures, broke none.
- Tried median filter + autocontrast: 98/100 vs 99/100 without; turned a correct 5 into S. Dropped.
- Remaining failures: province character on the strongest degradation (4), one 7/T, one US 0/O.

## AMD W7900D, full pipeline (score.py -> app.py -> server.py), 2026-11-14

| check | result | limit |
|---|---|---|
| score on samples | 200/200 | |
| time per image | 0.29-0.58 s | 30 s |
| server ready | 20 s (probably warm cache) | 10 min startup |
| peak VRAM | 17.2 GiB (17565 MB, 562 samples) | 1-48 GiB |

- torch is in /opt/venv on the base image; a separate venv can't see it -> install into /opt/venv (as the container will).
- requirements.txt: transformers==5.23.0 + accelerate, from pip freeze on this base. TODO: pin all added deps (before/after freeze diff).
- Open question: does the harness wait for anything (HEALTHCHECK?) before the first app.py call? If not, images lost ~ load time / 25 s. Measured load 20 s -> 0 lost.

## Status (2026-11-14): ready to build, waiting for an MI300X
- Done: prompt + fix_cn_serial, server/app pipeline, 200/200 on AMD W7900D, Dockerfile, .dockerignore, check_gates.sh
- Next: AMD Developer Cloud VM (1x MI300X, ROCm Software 10.1 image, on-demand) -> runbook in chat
- Blocked: "out of GPUs" in atl1 -> check devcloud.amd.com a few times a day
- Billing page shows "ACTION NEEDED" -> fix before the VM is available
- Deadline: challenges close 1 Dec; credits expire ~3 Dec
- Plan B if no GPU by ~20 Nov: build + push from Windows (Docker Desktop, WSL 2)
- TODO after push: move the Docker token out of ~/docker_credent.md