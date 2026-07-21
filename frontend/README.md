# AI Medical Imaging Platform — Frontend

React + Vite + Tailwind dashboard for the backend in `../backend`.

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173. Make sure the backend is running at the
URL in `.env` (`VITE_API_BASE_URL`, defaults to
`http://127.0.0.1:8000/api/v1`).

## What's here

- **Login / Signup** — `/login`
- **Dashboard** — patient roster, search, add patient (`/`)
- **Patient detail** — scans + reports for one patient, upload scan (`/patients/:id`)
- **Report viewer** — AI findings, scan + Grad-CAM heatmap, editable
  report fields (doctor review), PDF generate/download (`/reports/:id`)

## Design notes

Palette and type are deliberately clinical-instrument, not generic
SaaS: a cool paper canvas, a single desaturated teal accent (kept away
from the reds/ambers used for severity so status colors stay legible),
Fraunces for headers (reads like a printed report letterhead), IBM
Plex Sans/Mono for body and data. The signature element is
`ConfidenceTrace` — every AI confidence score renders as a thin
tick-marked trace rather than a generic progress bar, styled after an
oscilloscope/EKG strip, used consistently everywhere a score appears.

## Not built yet

- Analytics/dashboard charts, notifications, settings page
- Brain MRI/CT scan viewing beyond upload (no AI results for those yet — matches the backend)
- Patient history/timeline comparison view
