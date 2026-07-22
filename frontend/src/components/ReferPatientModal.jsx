import { useState } from "react";
import Modal from "./Modal";
import { referrals } from "../api/client";

export default function ReferPatientModal({ patientId, onClose, onReferred }) {
  const [toEmail, setToEmail] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const res = await referrals.create({ patient_id: patientId, to_email: toEmail, note });
      onReferred(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not send referral.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title="Refer Patient" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">Doctor's email</label>
          <input
            type="email"
            className="input mt-1"
            required
            value={toEmail}
            onChange={(e) => setToEmail(e.target.value)}
            placeholder="colleague@hospital.com"
          />
        </div>
        <div>
          <label className="label">Note (optional)</label>
          <textarea
            className="input mt-1 min-h-[70px] resize-y"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Reason for referral…"
          />
        </div>
        <p className="text-xs text-muted">
          They'll see this in their Incoming Referrals list and can accept
          or decline. You keep your own access either way.
        </p>
        {error && <p className="text-sm text-red">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "Sending…" : "Send referral"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
