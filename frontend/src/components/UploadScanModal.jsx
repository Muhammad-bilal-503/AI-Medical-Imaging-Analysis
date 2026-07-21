import { useState } from "react";
import Modal from "./Modal";
import { images } from "../api/client";

const SCAN_TYPES = [
  { value: "chest_xray", label: "Chest X-ray" },
  { value: "brain_mri", label: "Brain MRI" },
  { value: "brain_ct", label: "Brain CT" },
  { value: "chest_ct", label: "Chest CT" },
  { value: "abdomen_ct", label: "Abdomen CT" },
];

export default function UploadScanModal({ patientId, onClose, onUploaded }) {
  const [scanType, setScanType] = useState("chest_xray");
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const res = await images.upload(patientId, scanType, file);
      onUploaded(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <Modal title="Upload Scan" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">Scan type</label>
          <select
            className="input mt-1"
            value={scanType}
            onChange={(e) => setScanType(e.target.value)}
          >
            {SCAN_TYPES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
          {scanType !== "chest_xray" && (
            <p className="text-xs text-amber mt-1.5">
              AI analysis currently only runs for chest X-ray. This scan will
              be stored but won't get a prediction yet.
            </p>
          )}
        </div>
        <div>
          <label className="label">Image file</label>
          <input
            type="file"
            accept=".jpg,.jpeg,.png,.dcm"
            required
            className="input mt-1 file:mr-3 file:py-1.5 file:px-3 file:rounded-sm file:border-0 file:bg-teal-dim file:text-teal-deep file:text-sm"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>
        {error && <p className="text-sm text-red">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={uploading} className="btn-primary">
            {uploading ? "Uploading…" : "Upload"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
