# Medical Imaging Platform — Backend Scaffold

FastAPI + Supabase (Postgres + Auth + Storage) backend. This is the
foundation layer only: auth, RBAC, patient CRUD, image upload, and
report retrieval/editing. The AI pipeline (vision model, Grad-CAM,
LLM report generation) is stubbed with a TODO in `images.py` — that's
the natural next slice to build, as a background job so upload
requests don't block on inference.

## Setup

1. Create a Supabase project.
2. Run `supabase/schema.sql` in the SQL Editor (creates tables, RLS
   policies, indexes, triggers).
3. In Storage, create three **private** buckets: `medical-images`,
   `heatmaps`, `reports`.
4. Copy `.env.example` to `.env` and fill in the values from your
   project's "Connect to your project" panel (Server tab): `SUPABASE_URL`,
   `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_JWKS_URL`.
   New Supabase projects use this asymmetric-key setup instead of the old
   anon/service_role/JWT-secret trio — `security.py` verifies tokens
   against the JWKS endpoint rather than a shared secret.
5. Install and run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

6. Docs at `http://localhost:8000/docs`.

## AI pipeline (chest X-ray)

Uploading a `chest_xray` image now automatically runs, in the
background, after the upload responds:

1. Preprocessing (denoise, contrast-enhance, resize)
2. DenseNet121 inference — pretrained weights from
   [torchxrayvision](https://github.com/mlmed/torchxrayvision) (trained
   on NIH/CheXpert/MIMIC-CXR/PadChest/OpenI/Kaggle data). **Does not
   cover COVID-19 or Tuberculosis** — those labels weren't in the
   training data this model uses; flagging as a known gap vs. the
   original spec.
3. Grad-CAM heatmap generation, uploaded to the `heatmaps` bucket
4. A draft radiology report via Llama 3.1 8B (Groq) — saved with
   `status="ai_generated"`, **not** finalized; a doctor must review it
   (`PATCH /api/v1/reports/{id}`) before it's clinically usable.

You need a `GROQ_API_KEY` in `.env` (free tier at console.groq.com) for
step 4 to work — without it the pipeline still runs prediction +
Grad-CAM but throws on the report step (check the terminal logs; a
failed pipeline run currently fails silently to the end user, see the
TODO in `inference_service.py`).

**First run downloads the model weights** (~30MB, from GitHub) and
installing `torch`/`torchvision` is a multi-hundred-MB download — if
`pip install -r requirements.txt` is slow or times out, install torch's
CPU-only build first (much smaller than the default GPU build):
```powershell
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
```

Brain MRI / CT pipelines aren't built yet — those uploads store fine
but won't get a prediction until that's added.

## PDF reports

`POST /api/v1/reports/{report_id}/generate-pdf` renders the report —
patient/doctor info, the original scan + Grad-CAM heatmap, the AI
findings table, all report sections, a QR code, and a signature
placeholder — to PDF and stores it in the `reports` bucket. Works on
draft (`ai_generated`) reports too, clearly marked as a draft in the
PDF, so a doctor can print a working copy while reviewing.

`GET /api/v1/reports/{report_id}/pdf-url` returns a short-lived signed
URL to download it.

## Auth model

- **No public signup.** Accounts are admin-only. Run
  `python -m scripts.create_first_admin` once (from `backend/`) to
  create the first admin — after that, log in as them and use
  `POST /api/v1/admin/users` (or the frontend Admin panel) to create
  doctor/radiologist/other admin accounts. Each is created
  pre-confirmed with a password the admin hands them directly — no
  email link involved.
- Supabase Auth issues the JWT; `public.users` holds app-level role
  (`admin` / `doctor` / `radiologist`) and profile fields.
- Every route uses a **request-scoped client** (`get_user_client`)
  built from the caller's bearer token, so Postgres Row-Level Security
  enforces access — not just the API layer. The service-role client is
  reserved for backend-internal operations (background jobs, admin
  account management). A **separate legacy JWT client**
  (`get_legacy_admin_client`) exists solely for Supabase's Auth Admin
  API (`auth.admin.create_user` etc) — the new opaque secret key is
  rejected by that specific API ("User not allowed") even though it
  works for ordinary database/storage calls. Get this key from
  Project Settings > API > Legacy API Keys > service_role.
- `require_roles(...)` gives per-route RBAC on top of RLS.

## What's deliberately not here yet

- Vision model inference for brain MRI / CT — chest X-ray is done (see above).
- PDF generation, notifications, analytics endpoints.
- Background job runner (Celery/RQ or Supabase Edge Functions) for the
  upload → inference → report pipeline.
- DICOM parsing (pydicom) — currently only validates the file extension.

## Before this touches real patient data

This scaffold has no compliance work in it — RLS + JWT auth is a
baseline, not a certification. Handling real PHI means: a signed BAA
or equivalent with your hosting/DB provider, encryption-at-rest
verification, breach-notification procedures, and — since this
generates diagnostic output — checking whether Pakistan's DRAP or your
target market's regulator (FDA, MDR, etc.) classifies this as a
medical device requiring clearance before clinical use. Fine to build
and demo against synthetic/de-identified data in the meantime.
