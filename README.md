# Saree → Jacquard BMP Converter

Converts saree design images into weaving-ready jacquard shuttle BMPs.

Upload a saree image. Enter your loom dimensions (pins × cards) and the
number of shuttles. The app auto-detects the dominant colors, treats the
most common one as the background, and exports one 24-bit BMP per remaining
thread — black where the thread is active, white where it isn't.

Matches the conventional Indian brocade format (`jari`, `meena`, `resham`
naming, 24-bit RGB, black-on-white masks).

---

## Architecture

| Layer | Stack | Hosted on |
|-------|-------|-----------|
| Frontend | React + Vite + Tailwind CSS | Vercel |
| Backend | Python + FastAPI + OpenCV + Pillow + scikit-learn | Render |

The frontend is a static SPA. The backend is a long-running container
because k-means clustering and image processing don't fit in serverless
function timeouts.

```
.
├── backend/                 # FastAPI service
│   ├── app/
│   │   ├── api/             # HTTP route handlers
│   │   ├── processing/      # Image pipeline (validator, quantize, bmp_writer, ...)
│   │   ├── models/          # Pydantic schemas
│   │   ├── config.py        # Limits and defaults
│   │   └── main.py          # FastAPI app
│   ├── requirements.txt
│   └── render.yaml
├── frontend/                # React SPA
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── api/             # Backend client
│   │   ├── utils/           # Validators, zip reader
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
└── README.md
```

---

## How it works

1. **Validate** — reject corrupt files, unsupported formats, or images smaller than 500 px.
2. **Auto-resize** — if the upload is much larger than the target loom grid, downscale to roughly 2× the output dimensions (saves k-means compute with no quality loss).
3. **Bilateral filter** — smooth gradients while keeping motif edges sharp.
4. **Convert to LAB** — perceptually uniform color space; similar reds cluster together properly.
5. **K-means clustering** — with `K = num_shuttles + 1` clusters. The extra cluster is the auto-detected background.
6. **Sort palette by frequency** — most frequent cluster becomes the background; the rest are shuttles ordered by frequency.
7. **Cleanup** — kill isolated speckle pixels; optionally enforce a minimum motif size.
8. **Resize to exact pins × cards** — nearest-neighbor only (preserves palette indices).
9. **Write outputs**:
   - One 24-bit RGB BMP per shuttle, black = active.
   - A full-color preview PNG.
   - A `palette.json` mapping shuttle index → RGB color and pixel statistics.
10. **Zip and return** as `jacquard-output.zip`.

The background BMP is **not** exported — the "no thread fires" state is implicit (white in all shuttle BMPs at that pixel).

---

## Local development

You need Python 3.11+ and Node 18+ installed.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend is now serving at `http://localhost:8000`. Health check:
```
GET http://localhost:8000/api/health  →  {"status": "ok"}
```

### Frontend

In a separate terminal:

```bash
cd frontend
cp .env.example .env             # default points to localhost:8000, fine for dev
npm install
npm run dev
```

Frontend is now at `http://localhost:5173`. Open in browser, fill in the form, upload a saree image, click Convert.

---

## Deployment

### 1. Backend on Render

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com), create an account.
3. Click **New → Blueprint** and connect to your GitHub repo.
4. Render reads `backend/render.yaml` and provisions the service.
5. **Edit one env var before the first deploy succeeds**: set `ALLOWED_ORIGINS` to your future Vercel URL (e.g. `https://saree-jacquard.vercel.app`). You can update this later after the Vercel deploy.
6. Wait for the build. Note the service URL (e.g. `https://saree-jacquard-backend.onrender.com`).
7. Test it: `curl https://your-backend.onrender.com/api/health` should return `{"status": "ok"}`.

**Plan choice:**
- Free tier: backend sleeps after 15 minutes of inactivity, takes ~30 seconds to wake on first request. Fine for testing and very low usage.
- Starter ($7/mo): always on, no cold starts. Upgrade when real users hit the app.

### 2. Frontend on Vercel

1. Go to [vercel.com](https://vercel.com), create an account.
2. Click **New Project**, import your GitHub repo.
3. Vercel auto-detects the framework (Vite). **Set the Root Directory to `frontend`**.
4. In **Environment Variables**, add:
   - `VITE_API_URL` = your Render backend URL (e.g. `https://saree-jacquard-backend.onrender.com`)
5. Deploy.
6. Note your Vercel URL.

### 3. Update Render's CORS allowlist

Go back to Render's dashboard for the backend service. Edit `ALLOWED_ORIGINS` to include your Vercel URL. Render will redeploy automatically.

Open the Vercel URL — done.

---

## Pull request

When you push this code for the first time, use:

- **Branch:** `feat/saree-jacquard-bmp-converter`
- **PR title:** `feat: Saree-to-Jacquard BMP converter (v1)`

---

## Configuration

### Limits (in `backend/app/config.py`)

| Setting | Default | Range / notes |
|---------|---------|--------------|
| `MIN_PINS` / `MAX_PINS` | 1 / 10,000 | Output BMP width |
| `MIN_CARDS` / `MAX_CARDS` | 1 / 10,000 | Output BMP height |
| `MIN_SHUTTLES` / `MAX_SHUTTLES` | 2 / 8 | Number of thread BMPs |
| `MIN_INPUT_SHORT_EDGE` | 500 | Minimum upload size (px) |
| `MAX_INPUT_LONG_EDGE` | 8,000 | Auto-resize inputs larger than this |
| `MAX_UPLOAD_BYTES` | 50 MB | Upload byte cap |
| `PROCESSING_TIMEOUT_SECONDS` | 120 | Server-side processing timeout |
| `BILATERAL_*` | 9 / 75 / 75 | Bilateral filter strength |

### Default shuttle names

When N shuttles produce N BMPs, they're named by frequency:

| Shuttle # | Default filename |
|-----------|------------------|
| 1 | `resham.bmp` |
| 2 | `jari.bmp` |
| 3 | `meena.bmp` |
| 4+ | `shuttle_N.bmp` |

The user can rename each before downloading; defaults appear as editable text fields in the UI.

---

## API

### `POST /api/convert`

Multipart form upload. Fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `image` | File | yes | JPG / PNG / WEBP |
| `pins` | int | yes | 1–10,000 |
| `cards` | int | yes | 1–10,000 |
| `shuttles` | int | yes | 2–8 |
| `motif_cleanup` | bool | no | default `false` |
| `motif_min_size` | int | no | 1–5, default 2 |
| `shuttle_filenames` | string | no | JSON array, e.g. `'["red_silk","gold_zari"]'` |

**Response:** `application/zip` containing the BMPs, `preview.png`, and `palette.json`.

The `X-Palette-Metadata` response header contains JSON with the palette breakdown so the frontend can render swatches without unzipping client-side.

**Error response:** `422` or `500` with `{"detail": {"error": "...", "suggestion": "..."}}`.

---

## Future-ready architecture

Three stub modules are present and wired for future AI extensions:

- `backend/app/processing/motif_detection.py` — identify butis, paisleys, borders.
- `backend/app/processing/weave_prediction.py` — render realistic woven previews.
- `backend/app/processing/repeat_pattern.py` — detect/fix seamless repeats.

When these are implemented, they slot into the pipeline at well-defined points without restructuring the rest.

Notable v2 candidates not in v1:
- **Overlapping shuttle masks** (Approach B) for brocade-style highlights.
- **Custom palette mode** for mills with fixed thread color inventory.
- **Async job queue** for very large inputs (currently synchronous, 120 s cap).

---

## Limitations and known gotchas

- **Stretch-to-fit is unconditional.** The image is resized to exactly pins × cards regardless of aspect ratio. If you upload a square close-up but target a tall border BMP, the design will be vertically squashed. This is by design — matches loom workflows where the user knows what they're targeting.
- **Dithering is disabled.** Floyd-Steinberg-style dithering produces single-pixel shuttle changes that don't weave cleanly. Output is flat-color blocks per the loom's needs.
- **Disjoint masks only.** Each pixel belongs to exactly one shuttle. Brocade-style overlap (multiple threads at one intersection) is v2 work.
- **K-means is non-deterministic across libraries**, but with a fixed `random_state` (in `config.py`), the same input + settings produces the same output every time.
- **Render free tier sleeps.** First request after 15 min of inactivity takes ~30 seconds while the container wakes. Upgrade to Starter to fix.
