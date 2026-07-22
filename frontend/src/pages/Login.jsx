import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity } from "lucide-react";
import { auth } from "../api/client";

export default function Login({ onAuthed }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await auth.login(email, password);
      localStorage.setItem("access_token", res.data.access_token);
      await onAuthed();
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid email or password.");
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
          <h1 className="font-display text-xl mb-1">Log in</h1>
          <p className="text-sm text-muted mb-6">
            Accounts are provisioned by your admin. Contact them if you
            don't have credentials.
          </p>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input mt-1"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password"
                className="input mt-1"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-red">{error}</p>}
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? "Logging in…" : "Log in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
