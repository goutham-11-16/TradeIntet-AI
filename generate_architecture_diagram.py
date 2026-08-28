import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set high quality dark architecture diagram
plt.rcParams['font.family'] = 'Segoe UI'
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'DejaVu Sans']

fig, ax = plt.subplots(figsize=(16.8, 8.9), dpi=300)
fig.patch.set_facecolor('#0B1120')
ax.set_facecolor('#0B1120')

ax.axis('off')
ax.set_xlim(0, 16.8)
ax.set_ylim(0, 8.9)

def draw_node(x, y, w, h, title, subtitle="", items=[], bg_color="#131F37", border_color="#38BDF8", title_color="#FFFFFF", badge=""):
    glow = patches.FancyBboxPatch((x-0.04, y-0.04), w+0.08, h+0.08, boxstyle="round,pad=0.08,rounding_size=0.14",
                                  facecolor='none', edgecolor=border_color, linewidth=1.4, alpha=0.3)
    ax.add_patch(glow)
    
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.14",
                                 facecolor=bg_color, edgecolor=border_color, linewidth=1.8)
    ax.add_patch(box)
    
    if badge:
        ax.text(x + 0.25, y + h - 0.28, badge, color=border_color, fontsize=9.5, fontweight='bold', ha='left', va='center')
        ax.text(x + 1.15, y + h - 0.28, title, color=title_color, fontsize=11.5, fontweight='bold', ha='left', va='center')
    else:
        ax.text(x + w/2, y + h - 0.28, title, color=title_color, fontsize=11.5, fontweight='bold', ha='center', va='center')
        
    if subtitle:
        ax.text(x + w/2, y + h - 0.55, subtitle, color='#94A3B8', fontsize=8.5, style='italic', ha='center', va='center')
        start_y = y + h - 0.82
    else:
        start_y = y + h - 0.58
        
    for i, item in enumerate(items):
        ax.text(x + 0.22, start_y - i * 0.32, f"• {item}", color='#E2E8F0', fontsize=8.8, ha='left', va='center')

def draw_arrow(x1, y1, x2, y2, color="#38BDF8", lw=1.8):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, 
                                shrinkA=4, shrinkB=4, mutation_scale=13))

# Header Label
ax.text(8.4, 8.55, "TRADESENTINEL: AI BUSINESS AUTOMATION ARCHITECTURE", color='#38BDF8', fontsize=15, fontweight='bold', ha='center', va='center')
ax.text(8.4, 8.25, "End-to-End Autonomous Logistics Automation with Embedded VectorDB (PS4 Solution)", color='#94A3B8', fontsize=9.5, ha='center', va='center')

# Layer 1: USER & EVENTS (y: 6.75 - 7.95)
draw_node(0.6, 6.75, 4.8, 1.20, "Natural Language Input", "Business User Interface",
          ["'When risk > 70 & delay > 2d, reroute'", "Value > ₹10L requires manager approval"],
          bg_color="#1E293B", border_color="#60A5FA", title_color="#93C5FD", badge="[UI]")

draw_node(6.0, 6.75, 4.8, 1.20, "Automation Copilot UI", "Interactive Studio Canvas",
          ["Visual Workflow Studio (React Flow)", "One-Click Simulation & Live Exec"],
          bg_color="#1E293B", border_color="#60A5FA", title_color="#93C5FD", badge="[WEB]")

draw_node(11.4, 6.75, 4.8, 1.20, "Enterprise Event Stream", "Real-Time Triggers",
          ["Shipment Risk / Port Congestion Alert", "Carrier Delay / Customs Bottleneck"],
          bg_color="#1E293B", border_color="#60A5FA", title_color="#93C5FD", badge="[EVENT]")

# Layer 2: CORE AI & WORKFLOW ENGINES (y: 4.15 - 6.30)
draw_node(0.6, 4.15, 4.8, 2.15, "NL Workflow Parser", "AI Agent & DSL Compiler",
          ["Entity & Threshold Extraction", "Trigger-Condition-Action Parser", "Pydantic Graph DSL Schema", "LLM Prompt Reasoning (Claude / Ollama)"],
          bg_color="#0F243A", border_color="#0284C7", title_color="#38BDF8", badge="[AI]")

draw_node(6.0, 4.15, 4.8, 2.15, "Workflow Conflict Engine", "Deterministic & Semantic Safety",
          ["Approval Bypass & Collision Checks", "Vector Semantic Duplicate Matching", "Contradictory Action & Loop Detection", "Graph Cycle Analysis (Tarjan's Alg)"],
          bg_color="#2D1537", border_color="#EC4899", title_color="#F472B6", badge="[SAFETY]")

draw_node(11.4, 4.15, 4.8, 2.15, "Simulation & Exec Engine", "Dual-Mode Orchestration",
          ["Historical Replay (500+ Shipments)", "Delay & Cost Impact Prediction", "Step-by-Step DAG Execution", "Full Audit Trail & State Machine"],
          bg_color="#0D2E28", border_color="#10B981", title_color="#34D399", badge="[EXEC]")

# Layer 3: LOGISTICS INTELLIGENCE & VECTORDB (y: 2.05 - 3.70)
draw_node(0.6, 2.05, 15.6, 1.65, "Logistics Intelligence Toolbox & Embedded VectorDB (TradeSentinel Brain)", "Dense Semantic Embeddings + Deterministic ML Micro-Engines Exposed as Callable Agent Tools",
          ["Embedded VectorDB: Dense 128-dim Semantic Embeddings, Cosine Similarity Search, Zero-Config Persistent SQLite Store",
           "Predictive ML: compute_risk() [Port + Geopolitical + Customs], predict_eta(), predict_customs_delay(), root_cause_analysis()",
           "Optimization & Actions: optimize_routes(), calculate_financial_impact(), create_alert(), notify_ops_manager(), request_approval()"],
          bg_color="#131E38", border_color="#818CF8", title_color="#A5B4FC", badge="[VECTOR-DB]")

# Layer 4: LEARNING & GOVERNANCE (y: 0.45 - 1.60)
draw_node(0.6, 0.45, 4.8, 1.15, "Human-in-the-Loop", "Recovery Center",
          ["Operations Manager Authorization", "Safe Governance for Cargo > ₹10L"],
          bg_color="#261A35", border_color="#C084FC", title_color="#E9D5FF", badge="[AUTH]")

draw_node(6.0, 0.45, 4.8, 1.15, "Opportunity Detector", "Vector Pattern Discovery",
          ["Mines Logs via Vector Similarity Search", "1-Click Workflow Recommendations"],
          bg_color="#1A2E26", border_color="#34D399", title_color="#6EE7B7", badge="[DISCOVER]")

draw_node(11.4, 0.45, 4.8, 1.15, "Self-Optimizing Analytics", "Continuous Feedback Loop",
          ["Execution Latency & Bottlenecks", "Auto-Approval Policy Optimizer"],
          bg_color="#312E15", border_color="#FBBF24", title_color="#FDE68A", badge="[LEARN]")

# Connecting Arrows
draw_arrow(3.0, 6.75, 3.0, 6.30, color="#60A5FA")
draw_arrow(8.4, 6.75, 8.4, 6.30, color="#60A5FA")
draw_arrow(13.8, 6.75, 13.8, 6.30, color="#60A5FA")

draw_arrow(5.4, 5.22, 6.0, 5.22, color="#38BDF8")
draw_arrow(10.8, 5.22, 11.4, 5.22, color="#F472B6")

draw_arrow(3.0, 4.15, 3.0, 3.70, color="#818CF8")
draw_arrow(8.4, 4.15, 8.4, 3.70, color="#818CF8")
draw_arrow(13.8, 4.15, 13.8, 3.70, color="#818CF8")

draw_arrow(3.0, 2.05, 3.0, 1.60, color="#C084FC")
draw_arrow(8.4, 2.05, 8.4, 1.60, color="#34D399")
draw_arrow(13.8, 2.05, 13.8, 1.60, color="#FBBF24")

plt.tight_layout()
plt.savefig('tradesentinel_architecture.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
print("Generated VectorDB-enhanced tradesentinel_architecture.png")
