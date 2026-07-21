import { useState } from "react";
import Modal from "./Modal";
import { patients } from "../api/client";

export default function AddPatientModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    patient_code: "",
    full_name: "",
    date_of_birth: "",
    sex: "",
    contact_number: "",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function set(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = { ...form };
      if (!payload.date_of_birth) delete payload.date_of_birth;
      if (!payload.sex) delete payload.sex;
      if (!payload.contact_number) delete payload.contact_number;
      const res = await patients.create(payload);
      onCreated(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add patient.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title="Add Patient" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">Patient code</label>
          <input
            className="input mt-1"
            required
            value={form.patient_code}
            onChange={set("patient_code")}
            placeholder="e.g. P-014"
          />
        </div>
        <div>
          <label className="label">Full name</label>
          <input
            className="input mt-1"
            required
            value={form.full_name}
            onChange={set("full_name")}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Date of birth</label>
            <input
              type="date"
              className="input mt-1"
              value={form.date_of_birth}
              onChange={set("date_of_birth")}
            />
          </div>
          <div>
            <label className="label">Sex</label>
            <select className="input mt-1" value={form.sex} onChange={set("sex")}>
              <option value="">—</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
        <div>
          <label className="label">Contact number</label>
          <input
            className="input mt-1"
            value={form.contact_number}
            onChange={set("contact_number")}
          />
        </div>
        {error && <p className="text-sm text-red">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "Adding…" : "Add patient"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
