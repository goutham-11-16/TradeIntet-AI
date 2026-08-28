import { useQuery, useMutation } from "@tanstack/react-query";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StateWrap, RiskBadge, StatusBadge, ConfidenceBar, fmtMoney } from "@/components/common";
import {
  ArrowLeft, MapPin, Ship, Package, Building2, CheckCircle2, Circle,
  TrendingUp, TrendingDown, Minus, Sparkles, Loader2, Send,
} from "lucide-react";

const OutcomeIcon = ({ dir }) => dir === "down" ? <TrendingDown className="h-4 w-4 text-emerald-500" /> : dir === "up" ? <TrendingUp className="h-4 w-4 text-red-500" /> : <Minus className="h-4 w-4 text-muted-foreground" />;

export default function ShipmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { canManage } = useAuth();
  const [rec, setRec] = useState(null);
  const [genLoading, setGenLoading] = useState(false);
  const [custMsg, setCustMsg] = useState(null);
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["shipment", id], queryFn: () => api.shipment(id).then((r) => r.data) });

  const generate = async () => {
    setGenLoading(true);
    try {
      const { data } = await api.generateRec({ shipment_id: id });
      setRec(data.recommendation);
      toast.success("AI recovery recommendation generated");
    } catch (e) { toast.error(e.response?.data?.detail || "Failed"); }
    finally { setGenLoading(false); }
  };

  const genMessage = async () => {
    try {
      const { data } = await api.customerMessage({ shipment_id: id, eta_window: data?.eta_prediction ? `${data.eta_prediction.best_case} to ${data.eta_prediction.worst_case}` : "the coming days" });
      setCustMsg(data.message);
    } catch { toast.error("Failed to draft message"); }
  };

  return (
    <>
      <PageHeader testId="detail-header" title={`Shipment ${id}`} subtitle="Full tracking, prediction & recovery">
        <button onClick={() => navigate("/app/shipments")} className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-accent" data-testid="back-btn">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      </PageHeader>

      <StateWrap loading={isLoading} error={error ? "Shipment not found." : null} onRetry={refetch}>
        {data && (() => {
          const s = data.shipment; const eta = data.eta_prediction;
          return (
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Left column */}
              <div className="space-y-6 lg:col-span-2">
                {/* Overview */}
                <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="detail-overview">
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="font-heading text-lg font-bold">Overview</h2>
                    <div className="flex gap-2"><StatusBadge status={s.status} /><RiskBadge level={s.risk_category} score={s.risk_score} /></div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                    {[["Order ID", s.order_id, Package], ["Origin", s.origin, Ship], ["Destination", s.destination, MapPin],
                      ["Current Location", s.current_location, MapPin], ["Carrier", s.carrier, Building2], ["Method", s.shipping_method, Ship],
                      ["Category", s.product_category, Package], ["Value", fmtMoney(s.product_value), Package], ["Priority", s.customer_priority, Package]].map(([l, v, Icon]) => (
                      <div key={l}><p className="flex items-center gap-1.5 text-xs uppercase tracking-wide text-muted-foreground"><Icon className="h-3 w-3" />{l}</p><p className="mt-1 text-sm font-semibold">{v}</p></div>
                    ))}
                  </div>
                </div>

                {/* Timeline */}
                <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="detail-timeline">
                  <h2 className="mb-4 font-heading text-lg font-bold">Shipment Timeline</h2>
                  <div className="flex flex-col gap-0">
                    {data.timeline.map((t, i) => (
                      <div key={t.stage} className="flex items-center gap-3">
                        <div className="flex flex-col items-center">
                          {t.done ? <CheckCircle2 className="h-5 w-5 text-primary" /> : <Circle className={`h-5 w-5 ${t.current ? "text-primary" : "text-muted-foreground/40"}`} />}
                          {i < data.timeline.length - 1 && <div className={`h-8 w-0.5 ${t.done ? "bg-primary" : "bg-border"}`} />}
                        </div>
                        <span className={`text-sm ${t.current ? "font-bold text-primary" : t.done ? "font-medium" : "text-muted-foreground"}`}>{t.stage}{t.current && " (current)"}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* AI Recovery */}
                <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="detail-recovery">
                  <div className="mb-3 flex items-center justify-between">
                    <h2 className="font-heading text-lg font-bold">AI Recovery Recommendation</h2>
                    {canManage() && <button data-testid="generate-rec" onClick={generate} disabled={genLoading} className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">{genLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />} Generate</button>}
                  </div>
                  {rec ? (
                    <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
                      <p className="font-heading font-bold text-primary">{rec.action}</p>
                      <ul className="mt-2 space-y-1 text-sm text-muted-foreground">{rec.reasons.map((r, i) => <li key={i} className="flex gap-2"><span className="text-primary">•</span>{r}</li>)}</ul>
                      <p className="mt-3 text-sm">{rec.explanation}</p>
                      <div className="mt-3 flex gap-4 text-sm">
                        <span className="flex items-center gap-1">ETA <OutcomeIcon dir={rec.expected_outcome?.eta} /></span>
                        <span className="flex items-center gap-1">Risk <OutcomeIcon dir={rec.expected_outcome?.risk} /></span>
                        <span className="flex items-center gap-1">Cost <OutcomeIcon dir={rec.expected_outcome?.cost} /></span>
                      </div>
                      <Link to="/app/recovery" className="mt-3 inline-block text-sm font-semibold text-primary hover:underline">Review & approve in Recovery Center →</Link>
                    </div>
                  ) : <p className="text-sm text-muted-foreground">Generate an explainable recovery recommendation for this shipment. It requires manager approval before any action.</p>}
                </div>

                {/* Customer notification */}
                {canManage() && (
                  <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="detail-notify">
                    <div className="mb-3 flex items-center justify-between">
                      <h2 className="font-heading text-lg font-bold">Customer Notification</h2>
                      <button data-testid="draft-message" onClick={genMessage} className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent"><Send className="h-4 w-4" /> Draft</button>
                    </div>
                    {custMsg ? <><textarea data-testid="cust-message" className="w-full rounded-md border border-border bg-background p-3 text-sm" rows={3} value={custMsg} onChange={(e) => setCustMsg(e.target.value)} /><p className="mt-2 text-xs text-muted-foreground">Preview only. Requires manager approval before sending — not sent automatically.</p></> : <p className="text-sm text-muted-foreground">Draft a safe, non-committal delay notification for the customer.</p>}
                  </div>
                )}
              </div>

              {/* Right column */}
              <div className="space-y-6">
                {/* ETA prediction */}
                <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="detail-eta">
                  <h2 className="mb-4 font-heading text-lg font-bold">AI ETA Forecast</h2>
                  <div className="space-y-3">
                    {[["Best Case", eta.best_case, "text-emerald-500"], ["Most Likely", eta.most_likely, "text-primary"], ["Worst Case", eta.worst_case, "text-red-500"]].map(([l, v, c]) => (
                      <div key={l} className="flex items-center justify-between rounded-lg border border-border/60 bg-background p-3">
                        <span className="text-sm text-muted-foreground">{l}</span><span className={`font-mono text-sm font-bold ${c}`}>{v}</span>
                      </div>
                    ))}
                    <div className="rounded-lg border border-border/60 bg-background p-3">
                      <p className="mb-1 flex justify-between text-sm"><span className="text-muted-foreground">Delay Probability</span><span className="font-mono font-bold text-amber-500">{eta.delay_probability}%</span></p>
                      <p className="mb-1 text-xs text-muted-foreground">Confidence</p>
                      <ConfidenceBar value={eta.confidence} />
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-muted-foreground">Estimates only — not guaranteed.</p>
                </div>

                {/* Risk factors */}
                <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="detail-risk">
                  <h2 className="mb-1 font-heading text-lg font-bold">Risk Score: <span className="text-primary">{data.risk.score}/100</span></h2>
                  <p className="mb-4 text-xs text-muted-foreground">Category: {data.risk.category} · explainable breakdown</p>
                  <div className="space-y-2">
                    {Object.entries(data.risk.factors).map(([k, v]) => (
                      <div key={k}>
                        <div className="mb-1 flex justify-between text-xs"><span className="capitalize">{k}</span><span className="font-mono">{v} (+{data.risk.contributions[k]})</span></div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full bg-primary" style={{ width: `${v}%` }} /></div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Root cause */}
                <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="detail-rootcause">
                  <h2 className="mb-4 font-heading text-lg font-bold">Root-Cause Analysis</h2>
                  <div className="space-y-2">
                    {data.root_cause.map((r) => (
                      <div key={r.cause} className="flex items-center justify-between text-sm"><span>{r.cause}</span><span className="font-mono font-semibold">{r.contribution}%</span></div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })()}
      </StateWrap>
    </>
  );
}
