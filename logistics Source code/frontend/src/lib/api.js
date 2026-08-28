import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 
  (typeof window !== "undefined" && window.location.hostname !== "localhost" 
    ? "" 
    : "http://localhost:8001");
export const API = BACKEND_URL ? `${BACKEND_URL}/api` : "/api";

const client = axios.create({ baseURL: API, withCredentials: true });

// attach bearer token as fallback (cookies are primary)
client.interceptors.request.use((config) => {
  const t = localStorage.getItem("ts_token");
  if (t) config.headers.Authorization = `Bearer ${t}`;
  return config;
});

// Standalone fallback mock responses for Vercel production demo when backend is unreachable or blocked by CORS
const MOCK_FALLBACKS = {
  "/dashboard/overview": {
    kpis: {
      total_active: 126,
      at_risk: 14,
      high_risk: 7,
      predicted_delays: 12,
      avg_eta_days: 18.4,
      cost_exposure: 4820000,
      active_disruptions: 5,
      recovery_pending: 3
    },
    risk_overview: {
      global: 42,
      country: 45,
      port: 58,
      carrier: 34,
      customs: 46,
      geopolitical: 62,
      weather: 38
    },
    disruptions: [
      { id: "EVT-8801", title: "Singapore Port Anchorage Congestion", location: "Singapore Port", event_type: "Port Delay", severity: "High", detected_at: "2026-08-28T06:00:00Z" },
      { id: "EVT-8802", title: "Strait of Hormuz Security Advisory", location: "Strait of Hormuz", event_type: "Geopolitical", severity: "Warning", detected_at: "2026-08-28T05:30:00Z" },
      { id: "EVT-8803", title: "South China Sea Typhoon Warning", location: "South China Sea", event_type: "Weather", severity: "High", detected_at: "2026-08-28T04:15:00Z" }
    ],
    map_shipments: [
      { shipment_id: "TS-20260001", origin: "Shanghai Port", destination: "Rotterdam Port", origin_coords: [31.23, 121.47], dest_coords: [51.92, 4.47], risk_category: "High", status: "Delayed" },
      { shipment_id: "TS-20260002", origin: "Singapore Port", destination: "Los Angeles Port", origin_coords: [1.35, 103.81], dest_coords: [33.74, -118.27], risk_category: "Moderate", status: "In Transit" },
      { shipment_id: "TS-20260003", origin: "Ningbo Port", destination: "Hamburg Port", origin_coords: [29.86, 121.54], dest_coords: [53.55, 9.99], risk_category: "High", status: "Delayed" }
    ],
    ports: [
      { name: "Shanghai Port", lat: 31.23, lon: 121.47, status: "Congested" },
      { name: "Singapore Port", lat: 1.35, lon: 103.81, status: "Normal" },
      { name: "Rotterdam Port", lat: 51.92, lon: 4.47, status: "Normal" }
    ],
    prediction_chart: [
      { day: "Mon", historical_eta: 14, predicted_eta: 16, delay_probability: 35 },
      { day: "Tue", historical_eta: 14, predicted_eta: 17, delay_probability: 45 },
      { day: "Wed", historical_eta: 14, predicted_eta: 18, delay_probability: 60 },
      { day: "Thu", historical_eta: 14, predicted_eta: 16, delay_probability: 40 },
      { day: "Fri", historical_eta: 14, predicted_eta: 15, delay_probability: 25 }
    ]
  },
  "/analytics/overview": {
    on_time_rate: 94.2,
    cost_savings: 166600,
    hours_saved: 172,
    active_workflows: 8
  },
  "/shipments": {
    shipments: [
      { id: "TS-20260001", shipment_id: "TS-20260001", tracking_number: "BL-99201", origin: "Shanghai Port", destination: "Rotterdam Port", carrier: "Maersk Line", status: "Delayed", risk_score: 82, delay_days: 3.5, cargo_val: 1450000 },
      { id: "TS-20260002", shipment_id: "TS-20260002", tracking_number: "BL-99202", origin: "Singapore Port", destination: "Hamburg Port", carrier: "MSC", status: "On Time", risk_score: 18, delay_days: 0.0, cargo_val: 420000 },
      { id: "TS-20260003", shipment_id: "TS-20260003", tracking_number: "BL-99203", origin: "Ningbo Port", destination: "Los Angeles Port", carrier: "COSCO", status: "Delayed", risk_score: 74, delay_days: 2.8, cargo_val: 980000 }
    ],
    total: 3
  },
  "/alerts": {
    alerts: [
      { id: "ALT-9901", title: "Port Congestion Warning", level: "High", message: "Berth dwell time exceeded 3.8 days at Singapore Anchorage", shipment_id: "TS-20260001", read: false },
      { id: "ALT-9902", title: "Geopolitical Advisory", level: "Warning", message: "Strait of Hormuz Security Level 3 Advisory", shipment_id: "TS-20260004", read: false }
    ]
  },
  "/workflows": {
    workflows: [
      {
        id: "wf_168e80ffa843",
        name: "Auto Shipment Delayed -> Optimize Route",
        description: "Evaluates risk >= 70 & delay >= 2 days, optimizes alternate route, notifies manager, requires approval if value > ₹10L",
        status: "active",
        trigger: { type: "shipment_delayed" },
        nodes: [
          { id: "node_1", type: "TRIGGER", label: "Shipment Delayed Event" },
          { id: "node_2", type: "CONDITION", label: "Risk >= 70 & Delay >= 2.0d" },
          { id: "node_3", type: "ACTION", label: "Run ML Tool: Optimize Alternate Route", tool: "optimize_route" },
          { id: "node_4", type: "APPROVAL", label: "Logistics Manager Gate (> ₹10L)", approver_role: "manager" }
        ],
        edges: [
          { id: "e1", source: "node_1", target: "node_2" },
          { id: "e2", source: "node_2", target: "node_3" },
          { id: "e3", source: "node_3", target: "node_4" }
        ]
      }
    ]
  },
  "/integrations": {
    integrations: [
      { id: "shopify", name: "Shopify Plus", category: "E-commerce", description: "Bi-directional order sync", connected: true, records_synced: 18420, latency_ms: 38, health: "99.9%" },
      { id: "sap", name: "SAP S/4HANA", category: "ERP & SCM", description: "Enterprise resource planning sync", connected: true, records_synced: 42190, latency_ms: 64, health: "99.8%" },
      { id: "carrier-api", name: "Global AIS & Carrier Telemetry", category: "Carrier & AIS", description: "Live vessel AIS tracking", connected: true, records_synced: 145800, latency_ms: 22, health: "99.99%" }
    ]
  },
  "/integrations/events": {
    events: [
      { id: "EVT-88219", source: "Global AIS Telemetry", type: "ais.vessel_position_update", payload: "Vessel 'EVER GIVEN' passed Suez South Anchorage", timestamp: "2 mins ago", status: "Processed", matched_workflow: "Auto Shipment Delayed -> Optimize Route" },
      { id: "EVT-88218", source: "Shopify Plus", type: "shopify.order_created", payload: "New High-Priority Order #TS-9941 (Value: ₹1,420,000)", timestamp: "5 mins ago", status: "Processed", matched_workflow: "High Value Cargo Alert" }
    ]
  }
};

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || "";
    for (const [route, mockData] of Object.entries(MOCK_FALLBACKS)) {
      if (url.includes(route)) {
        console.warn(`[Vercel Standalone Mode] Serving fallback vector data for: ${route}`);
        return Promise.resolve({ data: mockData, status: 200, statusText: "OK", headers: {}, config: error.config });
      }
    }
    return Promise.reject(error);
  }
);

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
