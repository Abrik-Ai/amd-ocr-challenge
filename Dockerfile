# 1. BASE: start from the mandated image
FROM rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0

# 2. Work inside /app from here on
WORKDIR /app

# 3. Install our packages first (requirements.txt into /app, then pip install)
#    hint: torch lives in /opt/venv, so use that pip; add --no-cache-dir to keep the image smaller
COPY requirements.txt /app/
RUN /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt \
 && /opt/venv/bin/python3 -c "import torch; v = torch.__version__; print(v); assert '+rocm' in v, 'torch was replaced: ' + v"
# 5. Model weights (folder exists only on the build machine, after hf download)
COPY models/Qwen3-VL-8B-Instruct /models/Qwen3-VL-8B-Instruct

# 4. Our code into /app (the five .py files)
COPY app.py server.py ocr.py prompt.py /app/ 


# 6. Tell ocr.py / server.py where the model is
ENV MODEL_DIR=/models/Qwen3-VL-8B-Instruct

# 7. Healthcheck on the server's /health
#    hint: the command can be a python3 one-liner, like the one in the start script
HEALTHCHECK --interval=5s --timeout=3s --start-period=300s --retries=3 \
  CMD /opt/venv/bin/python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

# 8. On container start, run the server (it loads the model once, then serves)
CMD ["/opt/venv/bin/python3", "/app/server.py"]