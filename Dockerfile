FROM python:3.13-slim

WORKDIR /app

# Tesseract is required by pytesseract. OpenCV/RapidOCR also needs the GL and
# GLib runtime libraries even though this container does not display a GUI.
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import rapidocr_onnxruntime"

COPY . .

ENV FLASK_APP=run.py
EXPOSE 5000

CMD ["sh", "-c", "python -m app.schema_bootstrap && exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers ${WEB_CONCURRENCY:-2} --worker-class sync --timeout 180 --graceful-timeout 30 --keep-alive 5 --max-requests 500 --max-requests-jitter 50 --access-logfile - --error-logfile - run:app"]
