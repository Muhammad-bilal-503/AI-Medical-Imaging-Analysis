# AI Medical Imaging Analysis & Diagnostic Report Generation Platform

An AI-assisted clinical decision-support platform: upload a chest
X-ray, get a DenseNet121-based disease prediction with a Grad-CAM
explainability heatmap, and an AI-drafted radiology report (Llama 3.1
via Groq) for a doctor to review, edit, and finalize — with PDF export.

This is a clinical decision-support tool, not a replacement for a
licensed radiologist. AI-generated reports are drafts until reviewed
and signed off by a doctor.

## Structure

```
backend/    FastAPI + Supabase (Postgres, Auth, Storage) + the AI pipeline
frontend/   React + Vite + Tailwind dashboard
```

Each has its own README with setup instructions — start with
`backend/README.md`, then `frontend/README.md`.

## Stack

- **Backend:** FastAPI, Supabase (Postgres with row-level security,
  Auth, Storage), DenseNet121 (torchxrayvision, pretrained), Grad-CAM,
  Llama 3.1 8B (Groq), ReportLab (PDF generation)
- **Frontend:** React, Vite, Tailwind CSS, React Router

## Status

Backend, auth, RBAC, the full chest X-ray pipeline (upload → AI
prediction → heatmap → draft report → doctor review → PDF), and the
dashboard UI are working end to end. Brain MRI/CT prediction,
notifications, and analytics are not built yet.
