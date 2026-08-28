import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const client = axios.create({ baseURL: API, withCredentials: true });

// attach bearer token as fallback (cookies are primary)
client.interceptors.request.use((config) => {
  const t = localStorage.getItem("ts_token");
  if (t) config.headers.Authorization = `Bearer ${t}`;
  return config;
});

export function formatApiError(detail) {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export const api = {
  // auth
  login: (d) => client.post("/auth/login", d),
  register: (d) => client.post("/auth/register", d),
  logout: () => client.post("/auth/logout"),
  me: () => client.get("/auth/me"),
  forgot: (d) => client.post("/auth/forgot-password", d),
  reset: (d) => client.post("/auth/reset-password", d),
  // core
  dashboard: () => client.get("/dashboard/overview"),
  analytics: (days = 30) => client.get(`/analytics/overview?days=${days}`),
  shipments: (params = "") => client.get(`/shipments${params}`),
  shipment: (id) => client.get(`/shipments/${id}`),
  createShipment: (d) => client.post("/shipments", d),
  updateShipment: (id, d) => client.put(`/shipments/${id}`, d),
  deleteShipment: (id) => client.delete(`/shipments/${id}`),
  importCsv: (form) => client.post("/shipments/import/csv", form),
  exportCsvUrl: `${API}/shipments/export/csv`,
  // risk / predictions
  risks: () => client.get("/risks"),
  analyzeRisk: (d) => client.post("/risks/analyze", d),
  predictCustoms: (d) => client.post("/predictions/customs", d),
  predictEta: (d) => client.post("/predictions/eta", d),
  predictionPerformance: () => client.get("/predictions/performance"),
  // geo / impact / sim / routes / financial
  geoEvents: () => client.get("/geopolitical/events"),
  classifyEvent: (d) => client.post("/geopolitical/classify", d),
  analyzeImpact: (d) => client.post("/impact/analyze", d),
  simulate: (d) => client.post("/simulation/run", d),
  optimizeRoutes: (d) => client.post("/routes/optimize", d),
  financialImpact: (d) => client.post("/financial/impact", d),
  carriers: () => client.get("/carriers"),
  // recovery
  recommendations: (status = "") => client.get(`/recovery/recommendations${status ? `?status=${status}` : ""}`),
  generateRec: (d) => client.post("/recovery/generate", d),
  decideRec: (id, action, d) => client.post(`/recovery/${id}/${action}`, d),
  approvals: () => client.get("/approvals"),
  // alerts
  alerts: (params = "") => client.get(`/alerts${params}`),
  readAlert: (id) => client.post(`/alerts/${id}/read`),
  archiveAlert: (id) => client.post(`/alerts/${id}/archive`),
  readAllAlerts: () => client.post("/alerts/read-all"),
  // compliance
  compliance: (form) => client.post("/compliance/analyze", form),
  documents: () => client.get("/compliance/documents"),
  customerMessage: (d) => client.post("/notifications/customer", d),
  // reports / integrations / settings
  report: (t) => client.get(`/reports/${t}`),
  reportExportUrl: (t) => `${API}/reports/${t}/export`,
  reportPdfUrl: (t) => `${API}/reports/${t}/pdf`,
  resetDemo: () => client.post("/admin/reset-demo"),
  notifyAlert: (id) => client.post(`/alerts/${id}/notify`),
  testEmail: () => client.post("/notifications/test-email"),
  demoScenario: () => client.post("/demo/port-strike"),
  integrations: () => client.get("/integrations"),
  toggleIntegration: (id, config = null) => client.post(`/integrations/${id}/toggle`, config ? { config } : {}),
  syncIntegration: (id) => client.post(`/integrations/${id}/sync`),
  integrationEvents: () => client.get("/integrations/events"),
  updateProfile: (d) => client.put("/settings/profile", d),
  getPrefs: () => client.get("/settings/preferences"),
  setPrefs: (d) => client.put("/settings/preferences", d),
  // admin
  adminUsers: () => client.get("/admin/users"),
  updateRole: (id, role) => client.put(`/admin/users/${id}/role`, { role }),
  deleteUser: (id) => client.delete(`/admin/users/${id}`),
  auditLogs: () => client.get("/admin/audit-logs"),
  adminAnalytics: () => client.get("/admin/analytics"),
  // ─── AI Business Automation Copilot ───────────────────────
  generateWorkflow: (d) => client.post("/workflows/generate", d),
  validateWorkflow: (d) => client.post("/workflows/validate", d),
  simulateWorkflow: (d) => client.post("/workflows/simulate", d),
  executeWorkflow: (d) => client.post("/workflows/execute", d),
  workflows: () => client.get("/workflows"),
  workflow: (id) => client.get(`/workflows/${id}`),
  updateWorkflow: (id, d) => client.put(`/workflows/${id}`, d),
  deleteWorkflow: (id) => client.delete(`/workflows/${id}`),
  workflowRuns: (id) => client.get(`/workflows/${id}/runs`),
  workflowRun: (id) => client.get(`/workflow-runs/${id}`),
  approveStep: (id, d) => client.post(`/workflows/${id}/approve-step`, d),
  detectConflicts: (d) => client.post("/workflows/conflicts", d),
  allConflicts: () => client.get("/workflows/conflicts/all"),
  opportunities: () => client.get("/workflows/opportunities"),
  workflowAnalytics: () => client.get("/workflows/analytics"),
  optimizations: () => client.get("/workflows/optimizations"),
  applyOptimization: (id) => client.post(`/workflows/optimizations/${id}/apply`),
  seedDemoWorkflows: () => client.post("/workflows/demo/seed"),
  // vector database semantic search
  vectorSearch: (q, collection = "") => client.get(`/vectors/search?q=${encodeURIComponent(q)}${collection ? `&collection=${collection}` : ""}`),
};

export default client;
