import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader, fmtMoney, fmtNum, LevelBadge } from "@/components/common";
import { Loader2, FlaskConical, DollarSign } from "lucide-react";

const inputCls = "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary";

const SCENARIOS = [
  { name: "A: Continue Current Route", params: { disruption_duration_days: 7, port_closure: true, shipping_mode: "Sea" } },
  { name: "B: Reroute", params: { disruption_duration_days: 3, port_closure: false, customs_delay_days: 1, shipping_mode: "Sea" } },
  { name: "C: Change Carrier", params: { disruption_duration_days: 4, carrier_unavailable: false, shipping_mode: "Sea" } },
  { name: "D: Alternate Mode (Air)", params: { disruption_duration_days: 1, shipping_mode: "Air", fuel_cost_change_pct: 10 } },
];

export default function Simulator() {
  const [params, setParams] = useState({ disruption_duration_days: 7, port_closure: true, customs_delay_days: 2, carrier_unavailable: false, fuel_cost_change_pct: 0, shipping_mode: "Sea" });
  const [single, setSingle] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fin, setFin] = useState(null);

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await api.simulate({ params });
      setSingle(data);
      const { data: f } = await api.financialImpact({ affected_shipments: data.affected_shipments, avg_shipment_value: 4200, delay_days: data.average_delay_days });
      setFin(f);
    } catch { toast.error("Simulation failed"); }
    finally { setLoading(false); }
  };

  const compare = async () => {
    setLoading(true);
    try {
      const { data } = await api.simulate({ scenarios: SCENARIOS });
      setComparison(data.comparison);
    } catch { toast.error("Comparison failed"); }
    finally { setLoading(false); }
  };

  return (
    <>
      <PageHeader testId="sim-header" title="What-If Simulator" subtitle="Model disruption scenarios & compare recovery options" />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="sim-controls">
          <h2 className="mb-4 font-heading text-lg font-bold flex items-center gap-2"><FlaskConical className="h-5 w-5 text-primary" /> Scenario</h2>
          <div className="space-y-3">
            <label className="block text-sm">Disruption duration (days): {params.disruption_duration_days}
              <input data-testid="sim-duration" type="range" min="0" max="21" value={params.disruption_duration_days} onChange={(e) => setParams({ ...params, disruption_duration_days: Number(e.target.value) })} className="w-full accent-primary" /></label>
            <label className="block text-sm">Customs delay (days): {params.customs_delay_days}
              <input data-testid="sim-customs" type="range" min="0" max="10" value={params.customs_delay_days} onChange={(e) => setParams({ ...params, customs_delay_days: Number(e.target.value) })} className="w-full accent-primary" /></label>
            <label className="block text-sm">Fuel cost change (%): {params.fuel_cost_change_pct}
              <input data-testid="sim-fuel" type="range" min="-20" max="50" value={params.fuel_cost_change_pct} onChange={(e) => setParams({ ...params, fuel_cost_change_pct: Number(e.target.value) })} className="w-full accent-primary" /></label>
            <label className="flex items-center gap-2 text-sm"><input data-testid="sim-portclose" type="checkbox" checked={params.port_closure} onChange={(e) => setParams({ ...params, port_closure: e.target.checked })} className="h-4 w-4" /> Port closure</label>
            <label className="flex items-center gap-2 text-sm"><input data-testid="sim-carrier" type="checkbox" checked={params.carrier_unavailable} onChange={(e) => setParams({ ...params, carrier_unavailable: e.target.checked })} className="h-4 w-4" /> Carrier unavailable</label>
            <label className="block text-sm">Shipping mode
              <select data-testid="sim-mode" className={inputCls} value={params.shipping_mode} onChange={(e) => setParams({ ...params, shipping_mode: e.target.value })}>{["Sea", "Air", "Rail", "Road", "Express"].map((m) => <option key={m}>{m}</option>)}</select></label>
          </div>
          <button data-testid="run-sim" onClick={run} disabled={loading} className="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">{loading && <Loader2 className="h-4 w-4 animate-spin" />} Run Simulation</button>
          <button data-testid="compare-sim" onClick={compare} disabled={loading} className="mt-2 w-full rounded-md border border-border py-2 text-sm font-semibold hover:bg-accent">Compare Scenarios A–D</button>
        </div>

        <div className="space-y-6 lg:col-span-2">
          {single && (
            <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="sim-result">
              <h2 className="mb-4 font-heading text-lg font-bold">Simulation Result</h2>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                {[["Affected", fmtNum(single.affected_shipments)], ["Avg Delay", `${single.average_delay_days}d`], ["Add. Cost", fmtMoney(single.additional_cost)], ["Customers", fmtNum(single.customers_impacted)]].map(([l, v]) => (
                  <div key={l} className="rounded-lg border border-border/60 bg-background p-4 text-center"><p className="text-xs uppercase text-muted-foreground">{l}</p><p className="font-heading text-xl font-black">{v}</p></div>
                ))}
              </div>
              <p className="mt-4 flex items-center gap-2 text-sm">Risk level: <LevelBadge level={single.risk_level} /></p>
            </div>
          )}
          {fin && (
            <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="fin-result">
              <h2 className="mb-4 font-heading text-lg font-bold flex items-center gap-2"><DollarSign className="h-5 w-5 text-primary" /> Financial Impact Estimate</h2>
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-center"><p className="text-xs text-muted-foreground">Current Exposure</p><p className="font-heading text-lg font-black text-red-500">{fmtMoney(fin.estimated_current_exposure)}</p></div>
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-center"><p className="text-xs text-muted-foreground">After Recovery</p><p className="font-heading text-lg font-black text-amber-500">{fmtMoney(fin.estimated_exposure_after_recovery)}</p></div>
                <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4 text-center"><p className="text-xs text-muted-foreground">Cost Avoided</p><p className="font-heading text-lg font-black text-emerald-500">{fmtMoney(fin.potential_cost_avoided)}</p></div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
                {Object.entries(fin.breakdown).map(([k, v]) => <div key={k} className="flex justify-between rounded border border-border/60 px-2 py-1"><span className="capitalize text-muted-foreground">{k.replace(/_/g, " ")}</span><span className="font-mono">{fmtMoney(v)}</span></div>)}
              </div>
              <p className="mt-3 text-xs text-muted-foreground">{fin.note}</p>
            </div>
          )}
          {comparison && (
            <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="comparison-result">
              <h2 className="mb-4 font-heading text-lg font-bold">Scenario Comparison</h2>
              <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="border-b border-border/60 text-left text-xs uppercase text-muted-foreground"><tr><th className="px-3 py-2">Scenario</th><th className="px-3 py-2">Affected</th><th className="px-3 py-2">Avg Delay</th><th className="px-3 py-2">Add. Cost</th><th className="px-3 py-2">Risk</th></tr></thead>
                <tbody>{comparison.map((c) => (<tr key={c.name} className="border-b border-border/40"><td className="px-3 py-2 font-semibold">{c.name}</td><td className="px-3 py-2 font-mono">{fmtNum(c.affected_shipments)}</td><td className="px-3 py-2 font-mono">{c.average_delay_days}d</td><td className="px-3 py-2 font-mono">{fmtMoney(c.additional_cost)}</td><td className="px-3 py-2"><LevelBadge level={c.risk_level} /></td></tr>))}</tbody>
              </table></div>
            </div>
          )}
          {!single && !comparison && <div className="rounded-xl border border-dashed border-border/60 bg-card p-16 text-center text-sm text-muted-foreground">Configure a scenario and run the simulation.</div>}
        </div>
      </div>
    </>
  );
}
