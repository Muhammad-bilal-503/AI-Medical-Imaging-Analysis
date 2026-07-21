import { Link, useNavigate } from "react-router-dom";
import { Activity, LogOut } from "lucide-react";

export default function Navbar({ user }) {
  const navigate = useNavigate();

  function logout() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  return (
    <header className="border-b border-line bg-panel">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5">
          <Activity size={20} className="text-teal" strokeWidth={2.5} />
          <span className="font-display text-lg tracking-tight">
            AI Medical Imaging
          </span>
        </Link>
        {user && (
          <div className="flex items-center gap-4">
            <div className="text-right leading-tight">
              <div className="text-sm font-medium">{user.full_name}</div>
              <div className="text-xs text-muted capitalize">{user.role}</div>
            </div>
            <button
              onClick={logout}
              className="text-muted hover:text-red transition-colors"
              title="Log out"
            >
              <LogOut size={18} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
