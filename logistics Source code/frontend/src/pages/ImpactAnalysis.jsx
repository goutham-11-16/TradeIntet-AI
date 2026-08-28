import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader, StateWrap, RiskBadge, LevelBadge, fmtMoney, fmtNum } from "@/components/common";
import { Loader2, Radar, AlertTriangle, ArrowDown } from "lucide-react";

export default function ImpactAnalysis() {
  const [eventId, setEventId] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const { data } = useQuery({ queryKey: ["geo"], queryFn: () => api.geoEvents().then((r) => r.data) });

  const analyze = async (id) => {
    const chosen = id || eventId;
    if (!chosen) { toast.error("Select a disruption event"); return; }
    setLoading(true);
    try {
      const { data } = await api.analyzeImpact({ event_id: chosen });
      setResult(data);
    } catch (e) { toast.error(e.response?.data?.detail || "Analysis failed"); }
    finally { setLoading(false); }
  };

  return (
    <>
      <PageHeader testId="impact-header" title="Impact Analysis" subtitle="Identify shipments affected by a disruption & model the cascade" />
      <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="impact-selector">
        <label className="text-sm font-medium">Select a disruption event</label>
        <div className="mt-2 flex flex-col gap-3 sm:flex-row">
          <select data-testid="event-select" value={eventId} onChange={(e) => setEventId(e.target.value)}
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary">
            <option value="">Choose an event…</option>
            {data?.events?.map((e) => <option key={e.id} value={e.id}>{e.title} ({e.severity})</option>)}
          </select>
          <button data-testid="analyze-impact" onClick={() => analyze()} disabled={loading} className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60 sm:w-44">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Radar className="h-4 w-4" />} Analyze Impact
          </button>
        </div>
      </div>

      <StateWrap loading={loading} empty={!result && !loading} emptyText="Select an event and run impact analysis.">
        {result && (
          <div className="space-y-6" data-testid="impact-result">
            <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-5">
              <div className="mb-4 flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-500" /><h2 className="font-heading text-xl font-bold">{result.disruption.title}</h2><LevelBadge level={result.disruption.severity} /></div>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                {[["Affected", fmtNum(result.affected_count), "text-foreground"], ["High Risk", result.high_risk, "text-red-500"], ["Medium Risk", result.medium_risk, "text-amber-500"], ["Low Risk", result.low_risk, "text-emerald-500"]].map(([l, v, c]) => (
                  <div key={l} className="rounded-lg border border-border/60 bg-background p-4 text-center"><p className="text-xs uppercase text-muted-foreground">{l}</p><p className={`font-heading text-3xl font-black ${c}`}>{v}</p></div>
                ))}
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="rounded-lg border border-border/60 bg-background p-4"><p className="text-xs uppercase text-muted-foreground">Expected Delay</p><p className="font-heading text-2xl font-black text-amber-500">+{result.expected_delay_days}d</p></div>
                <div className="rounded-lg border border-border/60 bg-background p-4"><p className="text-xs uppercase text-muted-foreground">Est. Cost Exposure</p><p className="font-heading text-2xl font-black text-red-500">{fmtMoney(result.estimated_cost_exposure)}</p></div>
              </div>
            </div>

            {/* Cascade */}
            <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="cascade-chain">
              <h2 className="mb-4 font-heading text-lg font-bold">Cascading Disruption Analysis</h2>
              <div className="flex flex-col items-center gap-2">
                {result.cascade.levels.map((lvl, i) => (
                  <div key={lvl.level} className="w-full max-w-lg">
                    <div className="rounded-lg border border-border/60 bg-background p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wide text-primary">{lvl.label}</span>
                        <span className="font-mono text-sm font-bold">{fmtNum(lvl.affected)} shipments</span>
                      </div>
                      <p className="mt-1 text-sm font-semibold">{lvl.event}</p>
                      <p className="text-xs text-muted-foreground">{lvl.detail}</p>
                    </div>
                    {i < result.cascade.levels.length - 1 && <div className="flex justify-center py-1"><ArrowDown className="h-5 w-5 text-muted-foreground" /></div>}
                  </div>
                ))}
                <p className="mt-2 text-sm text-muted-foreground">Total estimated affected across the network: <span className="font-heading font-bold text-foreground">{fmtNum(result.cascade.total_estimated_affected)}</span></p>
              </div>
            </div>

            {/* Affected shipments */}
            <div className="rounded-xl border border-border/60 bg-card p-5">
              <h2 className="mb-3 font-heading text-lg font-bold">Affected Shipments ({result.affected_shipments.length})</h2>
              <div className="max-h-80 overflow-auto">
                <table className="w-full text-sm"><thead className="sticky top-0 border-b border-border/60 bg-card text-left text-xs uppercase text-muted-foreground"><tr><th className="px-3 py-2">Shipment</th><th className="px-3 py-2">Route</th><th className="px-3 py-2">Carrier</th><th className="px-3 py-2">Tier</th></tr></thead>
                  <tbody>{result.affected_shipments.map((s) => (
                    <tr key={s.shipment_id} className="border-b border-border/40 hover:bg-accent/40"><td className="px-3 py-2"><Link to={`/app/shipments/${s.shipment_id}`} className="font-mono text-primary hover:underline">{s.shipment_id}</Link></td><td className="px-3 py-2">{s.route}</td><td className="px-3 py-2">{s.carrier}</td><td className="px-3 py-2"><RiskBadge level={s.risk_tier === "High" ? "High" : s.risk_tier === "Medium" ? "Moderate" : "Low"} /></td></tr>
                  ))}</tbody>
                </table>
              </div>
              <Link to="/app/recovery" className="mt-3 inline-block text-sm font-semibold text-primary hover:underline">Generate recovery plans →</Link>
            </div>
          </div>
        )}
      </StateWrap>
    </>
  );
}
