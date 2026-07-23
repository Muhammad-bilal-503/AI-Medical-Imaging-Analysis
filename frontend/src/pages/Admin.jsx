import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { UserPlus, Users, FileText, ScanLine, Activity, ChevronRight } from "lucide-react";
import { admin } from "../api/client";
import CreateUserModal from "../components/CreateUserModal";

const ROLE_STYLES = {
  admin: "bg-red-bg text-red",
  doctor: "bg-teal-dim text-teal-deep",
  radiologist: "bg-amber-bg text-amber",
};

function StatCard({ icon: Icon, label, value, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`card p-5 flex items-center gap-4 text-left transition-colors ${
        active ? "border-teal bg-teal-dim/30" : "hover:border-teal/50"
      }`}
    >
      <div className="w-10 h-10 rounded-sm bg-teal-dim flex items-center justify-center shrink-0">
        <Icon size={18} className="text-teal" />
      </div>
      <div>
        <div className="font-display text-2xl leading-none">{value ?? "—"}</div>
        <div className="text-xs text-muted mt-1">{label}</div>
      </div>
    </button>
  );
}

export default function Admin() {
  const [view, setView] = useState("staff"); // "staff" | "patients"
  const [users, setUsers] = useState([]);
  const [patientsList, setPatientsList] = useState([]);
  const [stats, setStats] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [u, p, s] = await Promise.all([
        admin.listUsers(),
        admin.listPatients(),
        admin.stats(),
      ]);
      setUsers(u.data);
      setPatientsList(p.data);
      setStats(s.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function toggleActive(user) {
    const res = await admin.setActive(user.id, !user.is_active);
    setUsers(users.map((u) => (u.id === user.id ? res.data : u)));
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex items-end justify-between mb-8">
        <div>
          <p className="label mb-1">Admin</p>
          <h1 className="font-display text-3xl">Control Panel</h1>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <UserPlus size={16} />
          Create staff account
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        <StatCard
          icon={Users}
          label="Staff accounts"
          value={stats?.total_users}
          active={view === "staff"}
          onClick={() => setView("staff")}
        />
        <StatCard
          icon={Activity}
          label="Patients"
          value={stats?.total_patients}
          active={view === "patients"}
          onClick={() => setView("patients")}
        />
        <StatCard icon={ScanLine} label="Scans" value={stats?.total_scans} />
        <StatCard icon={FileText} label="Reports" value={stats?.total_reports} />
      </div>

      {view === "staff" && (
        <>
          <h2 className="font-display text-lg mb-3">Staff</h2>
          <div className="card divide-y divide-line">
            {loading && <div className="p-8 text-center text-sm text-muted">Loading…</div>}
            {!loading &&
              users.map((u) => (
                <div key={u.id} className="flex items-center justify-between px-5 py-4">
                  <div>
                    <div className="text-sm font-medium flex items-center gap-2">
                      {u.full_name}
                      {!u.is_active && (
                        <span className="text-xs text-muted font-normal">(deactivated)</span>
                      )}
                    </div>
                    <div className="text-xs text-muted font-mono mt-0.5">
                      {u.email}
                      {u.specialty ? ` · ${u.specialty}` : ""}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium capitalize ${
                        ROLE_STYLES[u.role] || ROLE_STYLES.doctor
                      }`}
                    >
                      {u.role}
                    </span>
                    <button
                      onClick={() => toggleActive(u)}
                      className="text-xs font-medium text-muted hover:text-teal"
                    >
                      {u.is_active ? "Deactivate" : "Reactivate"}
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </>
      )}

      {view === "patients" && (
        <>
          <h2 className="font-display text-lg mb-3">All Patients</h2>
          <div className="card divide-y divide-line">
            {loading && <div className="p-8 text-center text-sm text-muted">Loading…</div>}
            {!loading && patientsList.length === 0 && (
              <div className="p-8 text-center text-sm text-muted">No patients yet.</div>
            )}
            {!loading &&
              patientsList.map((p) => (
                <Link
                  key={p.id}
                  to={`/patients/${p.id}`}
                  className="flex items-center justify-between px-5 py-4 hover:bg-teal-dim/40 transition-colors"
                >
                  <div>
                    <div className="text-sm font-medium">{p.full_name}</div>
                    <div className="text-xs text-muted font-mono mt-0.5">{p.patient_code}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-xs text-muted text-right">
                      {p.doctors && p.doctors.length > 0 ? (
                        <span>Dr. {p.doctors.join(", ")}</span>
                      ) : (
                        <span className="italic">No doctor assigned</span>
                      )}
                    </div>
                    <ChevronRight size={16} className="text-muted shrink-0" />
                  </div>
                </Link>
              ))}
          </div>
        </>
      )}

      {showCreate && (
        <CreateUserModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            load();
          }}
        />
      )}
    </div>
  );
}
