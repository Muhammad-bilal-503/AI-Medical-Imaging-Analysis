import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, FileDown, Save, Loader2 } from "lucide-react";
import { patients, images as imagesApi, reports as reportsApi } from "../api/client";
import { StatusBadge, SeverityBadge } from "../components/StatusBadge";
import ConfidenceTrace from "../components/ConfidenceTrace";

const FIELDS = [
  ["examination", "Examination"],
  ["clinical_findings", "Clinical Findings"],
  ["image_findings", "Image Findings"],
  ["impression", "Impression"],
  ["recommendation", "Recommendation"],
  ["suggested_followup", "Suggested Follow-up"],
  ["confidence_summary", "Confidence Summary"],
];

export default function ReportViewer() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [patient, setPatient] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [scanUrl, setScanUrl] = useState(null);
  const [heatmapUrl, setHeatmapUrl] = useState(null);
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generatingPdf, setGeneratingPdf] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const r = await reportsApi.get(id);
      setReport(r.data);
      setForm(r.data);

      const [p, pred, scan] = await Promise.allSettled([
        patients.get(r.data.patient_id),
        imagesApi.prediction(r.data.image_id),
        imagesApi.signedUrl(r.data.image_id),
      ]);
      if (p.status === "fulfilled") setPatient(p.value.data);
      if (pred.status === "fulfilled") setPrediction(pred.value.data);
      if (scan.status === "fulfilled") setScanUrl(scan.value.data.url);

      try {
        const hm = await imagesApi.heatmapUrl(r.data.image_id);
        setHeatmapUrl(hm.data.url);
      } catch {
        /* heatmap may not exist yet */
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function setField(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  async function save() {
    setSaving(true);
    try {
      const payload = {};
      for (const [key] of FIELDS) payload[key] = form[key];
      const res = await reportsApi.update(id, payload);
      setReport(res.data);
    } finally {
      setSaving(false);
    }
  }

  async function generatePdf() {
    setGeneratingPdf(true);
    try {
      await reportsApi.generatePdf(id);
      const url = await reportsApi.pdfUrl(id);
      window.open(url.data.url, "_blank");
    } finally {
      setGeneratingPdf(false);
    }
  }

  if (loading) {
    return <div className="max-w-4xl mx-auto px-6 py-10 text-sm text-muted">Loading…</div>;
  }
  if (!report) return null;

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <Link
        to={patient ? `/patients/${patient.id}` : "/"}
        className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-teal mb-6"
      >
        <ArrowLeft size={15} />
        Back to patient
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <p className="label mb-1">{patient?.patient_code}</p>
          <h1 className="font-display text-3xl mb-2">
            {patient?.full_name || "Report"}
          </h1>
          <div className="flex items-center gap-2">
            <StatusBadge status={report.status} />
            <SeverityBadge severity={report.severity} />
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={generatePdf}
            disabled={generatingPdf}
            className="btn-secondary flex items-center gap-2"
          >
            {generatingPdf ? <Loader2 size={15} className="animate-spin" /> : <FileDown size={15} />}
            PDF
          </button>
          <button onClick={save} disabled={saving} className="btn-primary flex items-center gap-2">
            {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
            Save
          </button>
        </div>
      </div>

      {(scanUrl || heatmapUrl) && (
        <div className="grid grid-cols-2 gap-3 mb-8">
          {scanUrl && (
            <div className="card overflow-hidden">
              <img src={scanUrl} alt="Original scan" className="w-full aspect-square object-contain bg-ink/5" />
              <p className="text-xs text-muted text-center py-2 font-mono">Original scan</p>
            </div>
          )}
          {heatmapUrl && (
            <div className="card overflow-hidden">
              <img src={heatmapUrl} alt="Grad-CAM heatmap" className="w-full aspect-square object-contain bg-ink/5" />
              <p className="text-xs text-muted text-center py-2 font-mono">Grad-CAM attention</p>
            </div>
          )}
        </div>
      )}

      {prediction && (
        <div className="card p-5 mb-8">
          <h2 className="font-display text-lg mb-4">AI Vision Model Findings</h2>
          <div className="space-y-3">
            {prediction.predictions.slice(0, 8).map((p) => (
              <ConfidenceTrace key={p.label} label={p.label} confidence={p.confidence} />
            ))}
          </div>
        </div>
      )}

      <div className="card p-6 space-y-5">
        {FIELDS.map(([key, label]) => (
          <div key={key}>
            <label className="label">{label}</label>
            <textarea
              className="input mt-1.5 min-h-[70px] resize-y"
              value={form[key] || ""}
              onChange={setField(key)}
            />
          </div>
        ))}
      </div>

      <p className="text-xs text-muted mt-6">
        This report was drafted with AI assistance. It is decision support, not
        a standalone diagnosis, and must be reviewed before clinical use.
      </p>
    </div>
  );
}
