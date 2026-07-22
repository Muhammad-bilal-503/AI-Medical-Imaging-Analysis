import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search, UserPlus, ChevronRight, Inbox, Check, X } from "lucide-react";
import { patients, referrals } from "../api/client";
import AddPatientModal from "../components/AddPatientModal";

export default function Dashboard() {
  const [list, setList] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [incoming, setIncoming] = useState([]);

  async function load(query) {
    setLoading(true);
    try {
      const res = await patients.list(query);
      setList(res.data);
    } finally {
      setLoading(false);
    }
  }

  async function loadReferrals() {
    try {
      const res = await referrals.incoming();
      setIncoming(res.data);
    } catch {
      /* non-critical */
    }
  }

  useEffect(() => {
    load();
    loadReferrals();
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(q || undefined), 300);
    return () => clearTimeout(t);
  }, [q]);

  async function respond(id, action) {
    await (action === "accept" ? referrals.accept(id) : referrals.decline(id));
    setIncoming(incoming.filter((r) => r.id !== id));
    if (action === "accept") load(q || undefined);
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      {incoming.length > 0 && (
        <div className="card p-5 mb-8 border-l-2 border-l-amber">
          <div className="flex items-center gap-2 mb-3">
            <Inbox size={16} className="text-amber" />
            <h2 className="font-display text-lg">Incoming Referrals</h2>
          </div>
          <div className="space-y-2">
            {incoming.map((r) => (
              <div
                key={r.id}
                className="flex items-center justify-between bg-amber-bg/40 rounded-sm px-4 py-3"
              >
                <div>
                  <div className="text-sm font-medium">{r.patient_name}</div>
                  <div className="text-xs text-muted mt-0.5">
                    Referred by {r.referring_doctor_name}
                    {r.note ? ` — "${r.note}"` : ""}
                  </div>
                </div>
                <div className="flex gap-2 shrink-0 ml-3">
                  <button
                    onClick={() => respond(r.id, "accept")}
                    className="flex items-center gap-1 text-xs font-medium text-green bg-green-bg px-2.5 py-1.5 rounded-sm hover:opacity-80"
                  >
                    <Check size={13} />
                    Accept
                  </button>
                  <button
                    onClick={() => respond(r.id, "decline")}
                    className="flex items-center gap-1 text-xs font-medium text-red bg-red-bg px-2.5 py-1.5 rounded-sm hover:opacity-80"
                  >
                    <X size={13} />
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
