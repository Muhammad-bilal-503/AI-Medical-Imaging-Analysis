-- ============================================================
-- AI Medical Imaging Analysis Platform — Supabase Schema
-- Run in Supabase SQL Editor. Requires pgcrypto for gen_random_uuid().
-- ============================================================

create extension if not exists pgcrypto;

-- ---------- ENUMS ----------
create type user_role as enum ('admin', 'doctor', 'radiologist');
create type scan_type as enum ('chest_xray', 'brain_mri', 'brain_ct', 'chest_ct', 'abdomen_ct');
create type severity_level as enum ('low', 'moderate', 'high', 'critical');
create type report_status as enum ('pending', 'ai_generated', 'reviewed', 'finalized', 'amended');
create type referral_status as enum ('pending', 'accepted', 'declined');

-- ---------- USERS (extends Supabase auth.users) ----------
-- Supabase Auth owns auth.users (id, email, encrypted_password, etc).
-- This table stores app-level profile + role for RBAC.
create table public.users (
    id uuid primary key references auth.users(id) on delete cascade,
    email text unique,
    full_name text not null,
    role user_role not null default 'doctor',
    specialty text,
    license_number text,
    hospital_affiliation text,
    phone text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- ---------- PATIENTS ----------
create table public.patients (
    id uuid primary key default gen_random_uuid(),
    patient_code text unique not null,          -- human-readable MRN
    full_name text not null,
    date_of_birth date,
    sex text,
    contact_number text,
    email text,
    medical_history jsonb default '{}'::jsonb,   -- allergies, conditions, meds
    created_by uuid references public.users(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- ---------- PATIENT ACCESS ----------
-- Which doctors can see a given patient. A row is created for the
-- creating doctor when a patient is added, and for a referred doctor
-- once they accept a referral. This is what patient/image/report SELECT
-- RLS policies check — patients are private to the doctors who have
-- access, not visible to every authenticated doctor by default.
create table public.patient_access (
    patient_id uuid not null references public.patients(id) on delete cascade,
    doctor_id uuid not null references public.users(id) on delete cascade,
    granted_via text not null default 'owner',  -- 'owner' | 'referral'
    created_at timestamptz not null default now(),
    primary key (patient_id, doctor_id)
);

-- ---------- PATIENT REFERRALS ----------
create table public.patient_referrals (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid not null references public.patients(id) on delete cascade,
    referring_doctor_id uuid not null references public.users(id),
    referred_to_doctor_id uuid not null references public.users(id),
    note text,
    status referral_status not null default 'pending',
    created_at timestamptz not null default now(),
    responded_at timestamptz
);

-- ---------- MEDICAL IMAGES ----------
create table public.medical_images (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid not null references public.patients(id) on delete cascade,
    uploaded_by uuid not null references public.users(id),
    scan_type scan_type not null,
    storage_path text not null,                 -- Supabase Storage object path
    original_filename text not null,
    file_format text not null,                   -- jpg/png/dicom
    dicom_metadata jsonb,
    preprocessing jsonb default '{}'::jsonb,      -- resize/normalize/contrast params applied
    checksum text,
    uploaded_at timestamptz not null default now()
);

-- ---------- AI PREDICTIONS ----------
create table public.ai_predictions (
    id uuid primary key default gen_random_uuid(),
    image_id uuid not null references public.medical_images(id) on delete cascade,
    model_name text not null,                     -- e.g. densenet121-chestxray-v1
    model_version text not null,
    predictions jsonb not null,                   -- [{label, confidence}, ...]
    top_prediction text,
    top_confidence numeric(5,2),
    heatmap_storage_path text,                     -- Grad-CAM overlay image
    inference_time_ms integer,
    created_at timestamptz not null default now()
);

-- ---------- REPORTS ----------
create table public.reports (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid not null references public.patients(id) on delete cascade,
    image_id uuid not null references public.medical_images(id),
    prediction_id uuid references public.ai_predictions(id),
    doctor_id uuid references public.users(id),
    status report_status not null default 'pending',
    severity severity_level,
    examination text,
    clinical_findings text,
    image_findings text,
    impression text,
    recommendation text,
    suggested_followup text,
    confidence_summary text,
    llm_model text,                                -- e.g. llama-3.1-8b-instant
    pdf_storage_path text,
    doctor_notes text,
    finalized_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- ---------- FOLLOW-UP REPORTS ----------
create table public.follow_up_reports (
    id uuid primary key default gen_random_uuid(),
    original_report_id uuid not null references public.reports(id) on delete cascade,
    new_report_id uuid not null references public.reports(id) on delete cascade,
    comparison_notes text,
    disease_progression text,                       -- improved/stable/worsened
    created_by uuid references public.users(id),
    created_at timestamptz not null default now()
);

-- ---------- AUDIT LOGS ----------
create table public.audit_logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.users(id),
    action text not null,                            -- e.g. 'report.finalize', 'image.upload'
    resource_type text not null,
    resource_id uuid,
    ip_address text,
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz not null default now()
);

-- ---------- INDEXES ----------
create index idx_patients_patient_code on public.patients(patient_code);
create index idx_images_patient_id on public.medical_images(patient_id);
create index idx_predictions_image_id on public.ai_predictions(image_id);
create index idx_reports_patient_id on public.reports(patient_id);
create index idx_reports_status on public.reports(status);
create index idx_audit_logs_user_id on public.audit_logs(user_id);
create index idx_audit_logs_created_at on public.audit_logs(created_at desc);
create index idx_patient_access_doctor on public.patient_access(doctor_id);
create index idx_referrals_referred_to on public.patient_referrals(referred_to_doctor_id, status);
create index idx_referrals_referring on public.patient_referrals(referring_doctor_id);
create index idx_referrals_patient on public.patient_referrals(patient_id);

-- ---------- updated_at trigger helper ----------
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger trg_users_updated_at before update on public.users
    for each row execute function public.set_updated_at();
create trigger trg_patients_updated_at before update on public.patients
    for each row execute function public.set_updated_at();
create trigger trg_reports_updated_at before update on public.reports
    for each row execute function public.set_updated_at();

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
alter table public.users enable row level security;
alter table public.patients enable row level security;
alter table public.medical_images enable row level security;
alter table public.ai_predictions enable row level security;
alter table public.reports enable row level security;
alter table public.follow_up_reports enable row level security;
alter table public.audit_logs enable row level security;
alter table public.patient_access enable row level security;
alter table public.patient_referrals enable row level security;

-- Helper: current user's role
create or replace function public.current_user_role()
returns user_role as $$
  select role from public.users where id = auth.uid();
$$ language sql stable security definer;

-- Helpers for referrals.py's _enrich(): expose only a name, nothing
-- else, so a doctor who's been referred a patient (but doesn't have
-- patient_access yet) can still see who the referral is about.
create or replace function public.get_patient_name(p_id uuid)
returns text as $$
  select full_name from public.patients where id = p_id;
$$ language sql stable security definer;

create or replace function public.get_user_name(u_id uuid)
returns text as $$
  select full_name from public.users where id = u_id;
$$ language sql stable security definer;

grant execute on function public.get_patient_name(uuid) to authenticated;
grant execute on function public.get_user_name(uuid) to authenticated;

-- Auto-grant patient_access to the creating doctor, in the SAME
-- transaction as the patient insert. This matters: when an INSERT
-- has RETURNING (which supabase-py always requests), Postgres also
-- re-checks the new row against the table's SELECT policy before
-- handing it back — so without this trigger, the "doctors see
-- accessible patients" SELECT policy would reject the RETURNING
-- clause (no patient_access row exists yet at that instant), and the
-- whole INSERT fails with "new row violates row-level security
-- policy" even though the INSERT policy's own check passed.
create or replace function public.grant_patient_access_to_creator()
returns trigger as $$
begin
  if new.created_by is not null then
    insert into public.patient_access (patient_id, doctor_id, granted_via)
    values (new.id, new.created_by, 'owner')
    on conflict do nothing;
  end if;
  return new;
end;
$$ language plpgsql security definer;

create trigger trg_grant_patient_access
  after insert on public.patients
  for each row execute function public.grant_patient_access_to_creator();

-- Patients are private: visible only to doctors with explicit access
-- (the creator, or a doctor who accepted a referral), or admins.
-- Any authenticated doctor can still create a new patient.
create policy "doctors see accessible patients" on public.patients
    for select using (
        exists (
            select 1 from public.patient_access pa
            where pa.patient_id = patients.id and pa.doctor_id = auth.uid()
        )
        or public.current_user_role() = 'admin'
    );
create policy "staff can insert patients" on public.patients
    for insert with check (auth.role() = 'authenticated');

create policy "doctors see accessible patient images" on public.medical_images
    for select using (
        exists (
            select 1 from public.patient_access pa
            where pa.patient_id = medical_images.patient_id and pa.doctor_id = auth.uid()
        )
        or public.current_user_role() = 'admin'
    );
create policy "doctors upload to accessible patients" on public.medical_images
    for insert with check (
        exists (
            select 1 from public.patient_access pa
            where pa.patient_id = medical_images.patient_id and pa.doctor_id = auth.uid()
        )
    );

create policy "doctors see accessible patient predictions" on public.ai_predictions
    for select using (
        exists (
            select 1 from public.medical_images mi
            join public.patient_access pa on pa.patient_id = mi.patient_id
            where mi.id = ai_predictions.image_id and pa.doctor_id = auth.uid()
        )
        or public.current_user_role() = 'admin'
    );
create policy "staff can insert predictions" on public.ai_predictions
    for insert with check (auth.role() = 'authenticated');
-- Written by the background inference job via the secret-key client,
-- which (like Storage) does NOT bypass RLS under Supabase's new key
-- system — same reasoning as the storage policies above.

create policy "doctors see accessible patient reports" on public.reports
    for select using (
        exists (
            select 1 from public.patient_access pa
            where pa.patient_id = reports.patient_id and pa.doctor_id = auth.uid()
        )
        or public.current_user_role() = 'admin'
    );
create policy "staff can insert reports" on public.reports
    for insert with check (auth.role() = 'authenticated');
-- Written by the background inference job (AI draft) and by
-- generate-pdf's status updates — same secret-key-doesn't-bypass-RLS
-- reasoning as ai_predictions above.
create policy "doctors can update own or unassigned reports" on public.reports
    for update using (
        doctor_id = auth.uid()
        or doctor_id is null
        or public.current_user_role() = 'admin'
    );

-- Only admins manage user profiles directly; users can read their own row.
create policy "users read own profile" on public.users
    for select using (id = auth.uid() or public.current_user_role() = 'admin');
create policy "admins manage users" on public.users
    for all using (public.current_user_role() = 'admin');
create policy "staff can insert user profiles" on public.users
    for insert with check (auth.role() = 'authenticated');
-- Belt-and-suspenders: signup writes this row via the secret-key
-- client before the new user has any role recorded yet, so the
-- "admins manage users" check (current_user_role() = 'admin') doesn't
-- apply cleanly at that moment. This explicit policy covers it.

-- Follow-up reports: not written by any route yet, but the table
-- exists per the schema — same authenticated-staff pattern as the rest
-- so it isn't silently locked out once that feature is built.
create policy "staff can read follow ups" on public.follow_up_reports
    for select using (auth.role() = 'authenticated');
create policy "staff can insert follow ups" on public.follow_up_reports
    for insert with check (auth.role() = 'authenticated');

-- ---------- PATIENT ACCESS ----------
create policy "doctors see own access rows" on public.patient_access
    for select using (doctor_id = auth.uid() or public.current_user_role() = 'admin');
create policy "staff can grant access" on public.patient_access
    for insert with check (auth.role() = 'authenticated');
-- Granting happens in two places: patient creation (grants the
-- creator) and referral acceptance (grants the accepting doctor) —
-- both run as an authenticated user, never anonymously.

-- ---------- PATIENT REFERRALS ----------
create policy "doctors see referrals involving them" on public.patient_referrals
    for select using (
        referring_doctor_id = auth.uid()
        or referred_to_doctor_id = auth.uid()
        or public.current_user_role() = 'admin'
    );
create policy "doctors create referrals for their patients" on public.patient_referrals
    for insert with check (referring_doctor_id = auth.uid());
create policy "referred doctor responds to referral" on public.patient_referrals
    for update using (referred_to_doctor_id = auth.uid() or public.current_user_role() = 'admin');

-- Audit logs: append-only, admin-readable.
create policy "system inserts audit logs" on public.audit_logs
    for insert with check (auth.role() = 'authenticated');
create policy "admins read audit logs" on public.audit_logs
    for select using (public.current_user_role() = 'admin');

-- ============================================================
-- STORAGE POLICIES
-- Buckets themselves (medical-images, heatmaps, reports) must be
-- created in Storage first (private, not public) — this only covers
-- the Postgres RLS policies on storage.objects that gate access to
-- them. Without these, authenticated uploads get rejected with
-- "new row violates row-level security policy" even though the
-- bucket exists.
-- ============================================================
create policy "staff can upload medical images" on storage.objects
    for insert to authenticated
    with check (bucket_id = 'medical-images');
create policy "staff can read medical images" on storage.objects
    for select to authenticated
    using (bucket_id = 'medical-images');
create policy "staff can update medical images" on storage.objects
    for update to authenticated
    using (bucket_id = 'medical-images');

create policy "staff can upload heatmaps" on storage.objects
    for insert to authenticated
    with check (bucket_id = 'heatmaps');
create policy "staff can read heatmaps" on storage.objects
    for select to authenticated
    using (bucket_id = 'heatmaps');
create policy "staff can update heatmaps" on storage.objects
    for update to authenticated
    using (bucket_id = 'heatmaps');
-- Heatmap uploads happen via the "service" (secret-key) client in the
-- background job (inference_service.py). Unlike the old service_role
-- key, Supabase's new secret key does NOT automatically bypass Storage
-- RLS — it's still evaluated as `authenticated`, same as a normal user
-- token. So this insert policy is required, not optional.

create policy "staff can read reports" on storage.objects
    for select to authenticated
    using (bucket_id = 'reports');
create policy "staff can upload reports" on storage.objects
    for insert to authenticated
    with check (bucket_id = 'reports');
create policy "staff can update reports" on storage.objects
    for update to authenticated
    using (bucket_id = 'reports');
-- Same note as heatmaps: PDF generation writes via the secret-key
-- client, which still needs an explicit insert policy. UPDATE is
-- needed too — regenerating a PDF for the same report re-uses the same
-- storage path (x-upsert), which Supabase implements as an UPDATE
-- under the hood, not a second INSERT.
