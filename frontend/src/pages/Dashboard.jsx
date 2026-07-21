import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search, UserPlus, ChevronRight } from "lucide-react";
import { patients } from "../api/client";
import AddPatientModal from "../components/AddPatientModal";

export default function Dashboard() {
  const [list, setList] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  async function load(query) {
    setLoading(true);
    try {
      const res = await patients.list(query);
      setList(res.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(q || undefined), 300);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="flex items-end justify-between mb-8">
        <div>
          <p className="label mb-1">Patients</p>
          <h1 className="font-display text-3xl">Patient Roster</h1>
        </div>
        <button onClick={() => setShowAdd(true)} className="btn-primary flex items-center gap-2">
          <UserPlus size={16} />
          Add patient
        </button>
      </div>

      <div className="relative mb-6 max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input
          className="input pl-9"
          placeholder="Search by name or patient code…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      <div className="card divide-y divide-line">
        {loading && (
          <div className="p-8 text-center text-sm text-muted">Loading patients…</div>
        )}
        {!loading && list.length === 0 && (
          <div className="p-10 text-center">
            <p className="text-sm text-muted">
              No patients yet. Add one to start uploading scans.
            </p>
          </div>
        )}
        {!loading &&
          list.map((p) => (
            <Link
              key={p.id}
              to={`/patients/${p.id}`}
              className="flex items-center justify-between px-5 py-4 hover:bg-teal-dim/40 transition-colors group"
            >
              <div>
                <div className="font-medium text-ink">{p.full_name}</div>
                <div className="text-xs text-muted font-mono mt-0.5">
                  {p.patient_code}
                  {p.sex ? ` · ${p.sex}` : ""}
                  {p.date_of_birth ? ` · b. ${p.date_of_birth}` : ""}
                </div>
              </div>
              <ChevronRight
                size={18}
                className="text-muted group-hover:text-teal transition-colors"
              />
            </Link>
          ))}
      </div>

      {showAdd && (
        <AddPatientModal
          onClose={() => setShowAdd(false)}
          onCreated={(p) => {
            setShowAdd(false);
            setList([p, ...list]);
          }}
        />
      )}
    </div>
  );
}
