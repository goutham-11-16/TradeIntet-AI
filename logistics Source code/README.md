# TradeIntel AI — AI-Powered Business Automation Copilot

> **PS4: AI-Powered Business Automation Copilot**  
> **Team Name:** MARK42  
> **Team Members:** Goutham Reddy Esambadi (Leader), Kaniksha S, Elisetty Sowmya, Dutalluri Karimulla  
> **GitHub Repository:** [https://github.com/goutham-11-16/TradeIntet-AI.git](https://github.com/goutham-11-16/TradeIntet-AI.git)  
> **Live Production URL:** [https://trade-intet-ai-git-main-goutham-11-16s-projects.vercel.app](https://trade-intet-ai-git-main-goutham-11-16s-projects.vercel.app)

---

## 📄 Comprehensive Documentation
For full architectural specifications, workflow diagrams, API references, and module breakdowns, see the complete [**DOCUMENTATION.md**](DOCUMENTATION.md) file.

---

## 🌟 Key Highlights & Innovations

1. **Natural Language to DAG Copilot**: Converts plain-text business directives into executable Directed Acyclic Graph (DAG) automation workflows with triggers, conditions, tools, and approval gates.
2. **Multi-Rule Conflict Engine**: Detects rule overlaps, approval bypasses (e.g., cargo > ₹10L without manager sign-off), and race conditions before execution.
3. **Embedded VectorDB Engine**: Powered by persistent 128-dimensional dense embeddings with cosine similarity search for unstructured carrier advisories and historical playbooks.
4. **Interactive Ingestion & Webhook Stream**: Live telemetry hub connecting Shopify Plus, SAP S/4HANA, and global AIS vessel tracking.
5. **Human-in-the-Loop Recovery Engine**: Explainable AI recommendations allowing directors to approve, reject, or modify mitigation actions.

---

## 🚀 Quick Start Guide

### 1. Backend Setup
```bash
cd "logistics Source code/backend"
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8001
```

### 2. Frontend Setup
```bash
cd "logistics Source code/frontend"
npm install --legacy-peer-deps
npm start
```

### 🔐 Demo Logins
* **Admin**: `admin` / `admin123`
* **Manager**: `manager` / `manager123`
* **Viewer**: `viewer` / `viewer123`

---
*© 2026 Team MARK42 — CIT HackFusion PS4 Submission*
