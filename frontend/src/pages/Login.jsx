import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity } from "lucide-react";
import { auth } from "../api/client";

export default function Login({ onAuthed }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "doctor",
    specialty: "",
    license_number: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function set(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res =
        mode === "login"
          ? await auth.login(form.email, form.password)
          : await auth.signup(form);
      localStorage.setItem("access_token", res.data.access_token);
      await onAuthed();
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2.5 justify-center mb-8">
          <Activity size={22} className="text-teal" strokeWidth={2.5} />
          <span className="font-display text-xl tracking-tight">
            AI Medical Imaging
          </span>
        </div>

        <div className="card p-7">
          <div className="flex gap-1 mb-6 border-b border-line">
            {["login", "signup"].map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`pb-2.5 px-1 mr-5 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  mode === m
                    ? "border-teal text-teal"
                    : "border-transparent text-muted hover:text-ink"
                }`}
              >
                {m === "login" ? "Log in" : "Sign up"}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="space-y-4">
            {mode === "signup" && (
              <div>
                <label className="label">Full name</label>
                <input
                  className="input mt-1"
                  required
                  value={form.full_name}
                  onChange={set("full_name")}
                />
              </div>
            )}
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input mt-1"
                required
                value={form.email}
                onChange={set("email")}
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password"
                className="input mt-1"
                required
                minLength={8}
                value={form.password}
                onChange={set("password")}
              />
            </div>
            {mode === "signup" && (
              <>
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
                    <input
                      className="input mt-1"
                      value={form.specialty}
                      onChange={set("specialty")}
                    />
                  </div>
                  <div>
                    <label className="label">License #</label>
                    <input
                      className="input mt-1"
                      value={form.license_number}
                      onChange={set("license_number")}
                    />
                  </div>
                </div>
              </>
            )}
            {error && <p className="text-sm text-red">{error}</p>}
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
