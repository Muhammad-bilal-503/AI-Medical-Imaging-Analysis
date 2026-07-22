import { useState } from "react";
import Modal from "./Modal";
import { admin } from "../api/client";

export default function CreateUserModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "doctor",
    specialty: "",
    license_number: "",
    hospital_affiliation: "",
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
      const res = await admin.createUser(form);
      onCreated(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create account.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title="Create Staff Account" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">Full name</label>
          <input className="input mt-1" required value={form.full_name} onChange={set("full_name")} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Email</label>
            <input type="email" className="input mt-1" required value={form.email} onChange={set("email")} />
          </div>
          <div>
            <label className="label">Temporary password</label>
            <input
              type="text"
              className="input mt-1"
              required
              minLength={8}
              value={form.password}
              onChange={set("password")}
              placeholder="min 8 characters"
            />
          </div>
        </div>
        <div>
          <label className="label">Role</label>
          <select className="input mt-1" value={form.role} onChange={set("role")}>
            <option value="doctor">Doctor</option>
            <option value="radiologist">Radiologist</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Specialty</label>
            <input className="input mt-1" value={form.specialty} onChange={set("specialty")} />
          </div>
          <div>
            <label className="label">License #</label>
            <input className="input mt-1" value={form.license_number} onChange={set("license_number")} />
          </div>
        </div>
        <div>
          <label className="label">Hospital / affiliation</label>
          <input
            className="input mt-1"
            value={form.hospital_affiliation}
            onChange={set("hospital_affiliation")}
          />
        </div>
        <p className="text-xs text-muted">
          Share this email and password with them directly — the account
          is created pre-confirmed, no email link needed.
        </p>
        {error && <p className="text-sm text-red">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "Creating…" : "Create account"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
