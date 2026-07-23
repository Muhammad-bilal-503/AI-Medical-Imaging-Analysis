import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import PatientDetail from "./pages/PatientDetail";
import ReportViewer from "./pages/ReportViewer";
import Admin from "./pages/Admin";
import { auth } from "./api/client";

function RequireAuth({ user, children }) {
  if (!localStorage.getItem("access_token")) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [checked, setChecked] = useState(false);

  async function refreshUser() {
    if (!localStorage.getItem("access_token")) {
      setUser(null);
      setChecked(true);
      return;
    }
    try {
      const res = await auth.me();
      setUser(res.data);
    } catch {
      setUser(null);
    } finally {
      setChecked(true);
    }
  }

  useEffect(() => {
    refreshUser();
  }, []);

  if (!checked) return null;

  return (
    <BrowserRouter>
      {user && <Navbar user={user} />}
      <Routes>
        <Route path="/login" element={<Login onAuthed={refreshUser} />} />
        <Route
          path="/"
          element={
            <RequireAuth user={user}>
              {user?.role === "admin" ? <Navigate to="/admin" replace /> : <Dashboard />}
            </RequireAuth>
          }
        />
        <Route
          path="/patients/:id"
          element={
            <RequireAuth user={user}>
              <PatientDetail user={user} />
            </RequireAuth>
          }
        />
        <Route
          path="/reports/:id"
          element={
            <RequireAuth user={user}>
              <ReportViewer />
            </RequireAuth>
          }
        />
        <Route
          path="/admin"
          element={
            <RequireAuth user={user}>
              {user?.role === "admin" ? <Admin /> : <Navigate to="/" replace />}
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
