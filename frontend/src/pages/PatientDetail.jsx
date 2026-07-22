import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Upload, ImageIcon, FileText, Share2 } from "lucide-react";
import { patients, images as imagesApi, reports as reportsApi } from "../api/client";
import UploadScanModal from "../components/UploadScanModal";
import ReferPatientModal from "../components/ReferPatientModal";
import { StatusBadge, SeverityBadge } from "../components/StatusBadge";

const SCAN_LABELS = {
  chest_xray: "Chest X-ray",
  brain_mri: "Brain MRI",
  brain_ct: "Brain CT",
  chest_ct: "Chest CT",
  abdomen_ct: "Abdomen CT",
};

export default function PatientDetail() {
  const { id } = useParams();
  const [patient, setPatient] = useState(null);
  const [imgs, setImgs] = useState([]);
  const [reportList, setReportList] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [showRefer, setShowRefer] = useState(false);
  const [loading, setLoading] = useState(true);

  async function loadAll() {
    setLoading(true);
    try {
      const [p, i, r] = await Promise.all([
        patients.get(id),
        imagesApi.listForPatient(id),
        reportsApi.list({ patient_id: id }),
      ]);
      setPatient(p.data);
      setImgs(i.data);
      setReportList(r.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function reportForImage(imageId) {
    return reportList.find((r) => r.image_id === imageId);
  }

  if (loading) {
    return <div className="max-w-5xl mx-auto px-6 py-10 text-sm text-muted">Loading…</div>;
  }
  if (!patient) return null;

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex items-start justify-between mb-8">
        <div>
          <p className="label mb-1">{patient.patient_code}</p>
          <h1 className="font-display text-3xl mb-2">{patient.full_name}</h1>
          <p className="text-sm text-muted font-mono">
            {patient.sex && <span className="capitalize">{patient.sex}</span>}
            {patient.date_of_birth && ` · b. ${patient.date_of_birth}`}
            {patient.contact_number && ` · ${patient.contact_number}`}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowRefer(true)} className="btn-secondary flex items-center gap-2">
            <Share2 size={16} />
            Refer
          </button>
          <button onClick={() => setShowUpload(true)} className="btn-primary flex items-center gap-2">
            <Upload size={16} />
            Upload scan
          </button>
        </div>
      </div>

      <div>
        <h2 className="font-display text-lg mb-3">Scans</h2>
        {imgs.length === 0 ? (
          <div className="card p-8 text-center text-sm text-muted mb-8">
            No scans uploaded yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
            {imgs.map((img) => {
              const report = reportForImage(img.id);
              return (
                <div key={img.id} className="card p-4 flex items-center gap-3">
                  <div className="w-11 h-11 rounded-sm bg-teal-dim flex items-center justify-center shrink-0">
                    <ImageIcon size={18} className="text-teal" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">
                      {SCAN_LABELS[img.scan_type] || img.scan_type}
                    </div>
                    <div className="text-xs text-muted font-mono truncate">
                      {new Date(img.uploaded_at).toLocaleString()}
                    </div>
                  </div>
                  {report ? (
                    <Link
                      to={`/reports/${report.id}`}
                      className="text-xs font-medium text-teal hover:underline flex items-center gap-1 shrink-0"
                    >
                      <FileText size={14} />
                      View report
                    </Link>
                  ) : (
                    <span className="text-xs text-muted shrink-0">
                      {img.scan_type === "chest_xray" ? "Processing…" : "No AI report"}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div>
        <h2 className="font-display text-lg mb-3">Reports</h2>
        {reportList.length === 0 ? (
          <div className="card p-8 text-center text-sm text-muted">
            No reports yet — upload a chest X-ray to generate one.
          </div>
        ) : (
          <div className="card divide-y divide-line">
            {reportList.map((r) => (
              <Link
                key={r.id}
                to={`/reports/${r.id}`}
                className="flex items-center justify-between px-5 py-4 hover:bg-teal-dim/40 transition-colors"
              >
                <div>
                  <div className="text-sm font-medium">{r.examination || "Report"}</div>
                  <div className="text-xs text-muted font-mono mt-0.5">
                    {new Date(r.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={r.severity} />
                  <StatusBadge status={r.status} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {showUpload && (
        <UploadScanModal
          patientId={id}
          onClose={() => setShowUpload(false)}
          onUploaded={() => {
            setShowUpload(false);
            loadAll();
          }}
        />
      )}

      {showRefer && (
        <ReferPatientModal
          patientId={id}
          onClose={() => setShowRefer(false)}
          onReferred={() => setShowRefer(false)}
        />
      )}
    </div>
  );
}
