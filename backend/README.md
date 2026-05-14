# Backend — Saree → Jacquard BMP Converter

FastAPI service that converts saree images into weaving-ready jacquard shuttle BMPs.

Full project overview is in the [root README](../README.md). This file documents the backend specifically.

---

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify:
```bash
curl http://localhost:8000/api/health
# {"status":"ok"}
```

Interactive API docs at <http://localhost:8000/docs>.

---

## Module map

```
app/
├── main.py              FastAPI app + CORS + health check
├── config.py            All tunable limits and defaults
├── api/
│   └── convert.py       /api/convert route - form validation + response shaping
├── processing/
│   ├── pipeline.py      Orchestrator: bytes → zip bytes
│   ├── validator.py     Format / size / dimension checks
│   ├── preprocess.py    Auto-resize, bilateral filter, RGB↔LAB
│   ├── quantize.py      K-means in LAB, palette sorted by frequency
│   ├── cleanup.py       Speckle removal + min-motif-size enforcement
│   ├── resize.py        Nearest-neighbor stretch to pins × cards
│   ├── bmp_writer.py    24-bit BMP + preview PNG generation
│   ├── motif_detection.py    [stub - future AI]
│   ├── weave_prediction.py   [stub - future AI]
│   └── repeat_pattern.py     [stub - future AI]
└── models/
    └── schemas.py       Pydantic models
```

---

## Pipeline

`pipeline.run_pipeline()` is the single entry point. Given image bytes and settings, it returns zip bytes and palette metadata.

Each step is in its own module with a docstring explaining the reasoning. The pipeline is intentionally a flat list of calls, not a class hierarchy — it makes the flow obvious and each step trivially testable.

---

## Adding a new processing step

Drop a module in `app/processing/`, add a call site in `pipeline.run_pipeline()`. The pipeline orchestrator is short enough to read top-to-bottom.

Example: an "edge sharpening" step would slot between `apply_bilateral_filter` and `rgb_to_lab_pixels` in `pipeline.py`.

---

## Deployment

Render config is in `render.yaml`. See the root [README](../README.md) for the full deploy walkthrough.

Key things to remember:

- Set `ALLOWED_ORIGINS` env var to your Vercel URL after the first deploy.
- Free tier sleeps after 15 min idle (30 s wake time). Upgrade to Starter ($7/mo) for always-on.
- Health check path is `/api/health`.

---

## Testing manually

```bash
curl -X POST http://localhost:8000/api/convert \
  -F "image=@/path/to/saree.jpg" \
  -F "pins=480" \
  -F "cards=720" \
  -F "shuttles=4" \
  -o output.zip

unzip -l output.zip
# Should show resham.bmp, jari.bmp, meena.bmp, shuttle_4.bmp, preview.png, palette.json
```
