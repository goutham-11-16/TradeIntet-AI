import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader, fmtMoney } from "@/components/common";
import { Loader2, Route as RouteIcon, Trophy } from "lucide-react";

const inputCls = "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary";
const PRIORITIES = [
  ["balanced", "Balanced"], ["minimize_cost", "Minimize Cost"], ["minimize_time", "Fastest Delivery"],
  ["minimize_risk", "Lowest Risk"], ["maximize_resilience", "Max Resilience"],
];

export default function RouteOptimizer() {
  const [form, setForm] = useState({ origin: "Port of Shanghai", destination: "Port of Los Angeles" });
  const [priority, setPriority] = useState("balanced");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const optimize = async (p) => {
    setLoading(true);
    try {
      const { data } = await api.optimizeRoutes({ origin: form.origin, destination: form.destination, priority: p || priority });
      setResult(data);
    } catch { toast.error("Optimization failed"); }
    finally { setLoading(false); }
  };

  return (
    <>
      <PageHeader testId="route-header" title="Route Optimizer" subtitle="Compare alternatives on cost, ETA, risk & resilience" />
      <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="route-inputs">
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="text-sm">Origin<input data-testid="route-origin" className={inputCls} value={form.origin} onChange={(e) => setForm({ ...form, origin: e.target.value })} /></label>
          <label className="text-sm">Destination<input data-testid="route-dest" className={inputCls} value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })} /></label>
          <label className="text-sm">Priority
            <select data-testid="route-priority" className={inputCls} value={priority} onChange={(e) => { setPriority(e.target.value); if (result) optimize(e.target.value); }}>{PRIORITIES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
        </div>
        <button data-testid="optimize-btn" onClick={() => optimize()} disabled={loading} className="mt-4 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RouteIcon className="h-4 w-4" />} Optimize Routes</button>
      </div>

      {result && (
        <div className="space-y-6" data-testid="route-result">
          <div className="rounded-xl border border-primary/30 bg-primary/5 p-5">
            <div className="flex items-center gap-2"><Trophy className="h-5 w-5 text-primary" /><h2 className="font-heading text-lg font-bold">Recommended: {result.recommended.name}</h2></div>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-5">
              {[["Score", result.recommended.score], ["ETA", `${result.recommended.eta_days}d`], ["Cost", fmtMoney(result.recommended.cost)], ["Risk", result.recommended.risk], ["Resilience", result.recommended.resilience]].map(([l, v]) => (
                <div key={l} className="rounded-lg border border-border/60 bg-background p-3 text-center"><p className="text-xs uppercase text-muted-foreground">{l}</p><p className="font-heading text-lg font-black">{v}</p></div>
              ))}
            </div>
            <p className="mt-3 text-sm text-muted-foreground">Optimized for <span className="font-semibold text-foreground">{PRIORITIES.find(([v]) => v === result.priority)?.[1]}</span>. Higher score is better.</p>
          </div>

          <div className="rounded-xl border border-border/60 bg-card p-5">
            <h2 className="mb-3 font-heading text-lg font-bold">All Route Options</h2>
            <div className="overflow-x-auto"><table className="w-full text-sm" data-testid="route-table"><thead className="border-b border-border/60 text-left text-xs uppercase text-muted-foreground"><tr><th className="px-3 py-2">Route</th><th className="px-3 py-2">ETA</th><th className="px-3 py-2">Cost</th><th className="px-3 py-2">Risk</th><th className="px-3 py-2">Resilience</th><th className="px-3 py-2">Score</th></tr></thead>
              <tbody>{result.routes.map((r, i) => (
                <tr key={r.name} className={`border-b border-border/40 ${i === 0 ? "bg-primary/5" : ""}`}><td className="px-3 py-2 font-semibold">{r.name}</td><td className="px-3 py-2 font-mono">{r.eta_days}d</td><td className="px-3 py-2 font-mono">{fmtMoney(r.cost)}</td><td className="px-3 py-2 font-mono">{r.risk}</td><td className="px-3 py-2 font-mono">{r.resilience}</td><td className="px-3 py-2"><span className="rounded bg-primary/10 px-2 py-0.5 font-mono font-bold text-primary">{r.score}</span></td></tr>
              ))}</tbody>
            </table></div>
          </div>
        </div>
      )}
      {!result && !loading && <div className="rounded-xl border border-dashed border-border/60 bg-card p-16 text-center text-sm text-muted-foreground">Enter route details and optimize.</div>}
    </>
  );
}
