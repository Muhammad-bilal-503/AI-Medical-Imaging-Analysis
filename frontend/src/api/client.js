import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

const client = axios.create({ baseURL: BASE_URL });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export const auth = {
  login: (email, password) => client.post("/auth/login", { email, password }),
  me: () => client.get("/auth/me"),
};

export const referrals = {
  create: (payload) => client.post("/referrals", payload),
  incoming: () => client.get("/referrals/incoming"),
  outgoing: () => client.get("/referrals/outgoing"),
  accept: (id) => client.post(`/referrals/${id}/accept`),
  decline: (id) => client.post(`/referrals/${id}/decline`),
};

export const admin = {
  listUsers: () => client.get("/admin/users"),
  listPatients: () => client.get("/admin/patients"),
  createUser: (payload) => client.post("/admin/users", payload),
  setActive: (userId, isActive) =>
    client.patch(`/admin/users/${userId}/active`, null, {
      params: { is_active: isActive },
    }),
  stats: () => client.get("/admin/stats"),
};

export const patients = {
  list: (q) => client.get("/patients", { params: q ? { q } : {} }),
  get: (id) => client.get(`/patients/${id}`),
  create: (payload) => client.post("/patients", payload),
};

export const images = {
  listForPatient: (patientId) => client.get(`/images/patient/${patientId}`),
  signedUrl: (imageId) => client.get(`/images/${imageId}/signed-url`),
  heatmapUrl: (imageId) => client.get(`/images/${imageId}/heatmap-url`),
  prediction: (imageId) => client.get(`/images/${imageId}/prediction`),
  upload: (patientId, scanType, file) => {
    const form = new FormData();
    form.append("patient_id", patientId);
    form.append("scan_type", scanType);
    form.append("file", file);
    return client.post("/images/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export const reports = {
  list: (params) => client.get("/reports", { params }),
  get: (id) => client.get(`/reports/${id}`),
  update: (id, payload) => client.patch(`/reports/${id}`, payload),
  generatePdf: (id) => client.post(`/reports/${id}/generate-pdf`),
  pdfUrl: (id) => client.get(`/reports/${id}/pdf-url`),
};

export default client;
