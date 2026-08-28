import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { PageHeader, StateWrap, RiskBadge, fmtMoney } from "@/components/common";
import { Sliders } from "lucide-react";

const LABELS = { port: "Port", customs: "Customs", geopolitical: "Geopolitical", carrier: "Carrier", route: "Route", weather: "Weather" };

export default function RiskIntelligence() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["risks"], queryFn: () => api.risks().then((r) => r.data) });
  const [weights, setWeights] = useState(null);
  const [factors, setFactors] = useState({ port: 60, customs: 55, geopolitical: 50, carrier: 40, route: 45, weather: 30 });
  const [result, setResult] = useState(null);

  useEffect(() => { if (data?.default_weights && !weights) setWeights(data.default_weights); }, [data, weights]);

  const analyze = async () => {
    const { data } = await api.analyzeRisk({ factors, weights });
    setResult(data);
  };

  return (
    <>
      <PageHeader testId="risk-header" title="Risk Intelligence" subtitle="Unified, explainable risk scoring across corridors" />
      <StateWrap loading={isLoading} error={error ? "Failed to load risk data." : null} onRetry={refetch}>
        {data && (
          <div className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Configurable risk calculator */}
              <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="risk-calculator">
                <h2 className="mb-1 font-heading text-lg font-bold flex items-center gap-2"><Sliders className="h-5 w-5 text-primary" /> Risk Score Calculator</h2>
                <p className="mb-4 text-xs text-muted-foreground">Adjust factor values and weights, then compute the unified score.</p>
                <div className="space-y-3">
                  {Object.keys(factors).map((k) => (
                    <div key={k}>
                      <div className="mb-1 flex justify-between text-xs"><span>{LABELS[k]} risk</span><span className="font-mono">{factors[k]} · w {weights?.[k]?.toFixed(2)}</span></div>
                      <input data-testid={`factor-${k}`} type="range" min="0" max="100" value={factors[k]} onChange={(e) => setFactors({ ...factors, [k]: Number(e.target.value) })} className="w-full accent-primary" />
                      {weights && <input type="range" min="0" max="0.5" step="0.02" value={weights[k]} onChange={(e) => setWeights({ ...weights, [k]: Number(e.target.value) })} className="w-full accent-amber-500" />}
                    </div>
                  ))}
                </div>
                <button data-testid="compute-risk" onClick={analyze} className="mt-4 w-full rounded-md bg-primary py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90">Compute Risk Score</button>
                {result && (
                  <div className="mt-4 rounded-lg border border-primary/30 bg-primary/5 p-4" data-testid="risk-result">
                    <p className="font-heading text-3xl font-black text-primary">{result.score}<span className="text-lg text-muted-foreground">/100</span></p>
                    <p className="text-sm"><RiskBadge level={result.category} /></p>
                    <div className="mt-3 space-y-1 text-xs">{Object.entries(result.contributions).map(([k, v]) => <div key={k} className="flex justify-between"><span className="capitalize">{LABELS[k]}</span><span className="font-mono">+{v}</span></div>)}</div>
                  </div>
                )}
              </div>

              {/* Port & carrier risk */}
              <div className="space-y-6">
                <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="port-risk">
                  <h2 className="mb-3 font-heading text-lg font-bold">Port Risk</h2>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {data.ports.sort((a, b) => b.risk_score - a.risk_score).map((p) => (
                      <div key={p.code} className="flex items-center justify-between rounded-md border border-border/60 bg-background px-3 py-2 text-sm">
                        <span>{p.name}</span><span className="font-mono text-muted-foreground">cong {p.congestion}%</span>
                        <RiskBadge level={p.risk_score >= 60 ? "High" : p.risk_score >= 40 ? "Moderate" : "Low"} score={Math.round(p.risk_score)} />
                      </div>
                    ))}
                  </div>
                </div>
                <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="carrier-risk">
                  <h2 className="mb-3 font-heading text-lg font-bold">Carrier Risk</h2>
                  <div className="space-y-2">
                    {data.carriers.map((c) => (
                      <div key={c.id} className="flex items-center justify-between rounded-md border border-border/60 bg-background px-3 py-2 text-sm">
                        <span>{c.name}</span><span className="font-mono text-emerald-500">{c.on_time_pct}% on-time</span>
                        <RiskBadge level={c.risk_score >= 25 ? "Moderate" : "Low"} score={Math.round(c.risk_score)} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Top risk shipments */}
            <div className="rounded-xl border border-border/60 bg-card p-5">
              <h2 className="mb-3 font-heading text-lg font-bold">Highest-Risk Shipments</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="top-risk-table">
                  <thead className="border-b border-border/60 text-left text-xs uppercase text-muted-foreground"><tr><th className="px-3 py-2">Shipment</th><th className="px-3 py-2">Route</th><th className="px-3 py-2">Value</th><th className="px-3 py-2">Risk</th></tr></thead>
                  <tbody>
                    {data.top_risk_shipments.map((s) => (
                      <tr key={s.shipment_id} className="border-b border-border/40 hover:bg-accent/40">
                        <td className="px-3 py-2"><Link to={`/app/shipments/${s.shipment_id}`} className="font-mono font-semibold text-primary hover:underline">{s.shipment_id}</Link></td>
                        <td className="px-3 py-2">{s.origin} → {s.destination}</td>
                        <td className="px-3 py-2 font-mono">{fmtMoney(s.product_value)}</td>
                        <td className="px-3 py-2"><RiskBadge level={s.risk_category} score={s.risk_score} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </StateWrap>
    </>
  );
}
