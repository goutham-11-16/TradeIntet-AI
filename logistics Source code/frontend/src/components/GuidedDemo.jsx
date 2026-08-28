import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { LevelBadge, RiskBadge, ConfidenceBar, fmtMoney, fmtNum } from "@/components/common";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Radar, Brain, AlertTriangle, LifeBuoy, ArrowRight, ArrowLeft, Loader2, Check, Play, Sparkles,
} from "lucide-react";

const STEPS = [
  { key: "detect", label: "Detect", icon: Radar },
  { key: "predict", label: "Predict", icon: Brain },
  { key: "impact", label: "Assess Impact", icon: AlertTriangle },
  { key: "recover", label: "Recover", icon: LifeBuoy },
];

export default function GuidedDemo({ open, onOpenChange }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [step, setStep] = useState(0);
  const [approved, setApproved] = useState(false);
  const [approving, setApproving] = useState(false);

  const run = async () => {
    setLoading(true); setApproved(false); setStep(0);
    try {
      const { data } = await api.demoScenario();
      setData(data);
    } catch { toast.error("Failed to run scenario"); }
    finally { setLoading(false); }
  };

  const approve = async () => {
    setApproving(true);
    try {
      await api.decideRec(data.recover.id, "approve", { reason: "Approved via guided live demo" });
      setApproved(true);
      toast.success("Recovery plan approved — shipment ETA updated");
    } catch (e) { toast.error(e.response?.data?.detail || "Approval failed"); }
    finally { setApproving(false); }
  };

  const reset = () => { setData(null); setStep(0); setApproved(false); };

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (!o) reset(); }}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl" data-testid="guided-demo">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-primary" /> Live Disruption Scenario — Port of LA Strike</DialogTitle>
        </DialogHeader>

        {!data ? (
          <div className="py-8 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Radar className="h-8 w-8" /></div>
            <p className="mt-4 text-sm text-muted-foreground">Watch TradeIntel AI respond to a critical port strike in real time: <br /><span className="font-semibold text-foreground">Detect -> Predict -> Assess Impact -> Recover</span></p>
            <button data-testid="demo-run" onClick={run} disabled={loading} className="mt-6 inline-flex items-center gap-2 rounded-md bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />} Run Live Demo
            </button>
          </div>
        ) : (
          <div>
            {/* Stepper */}
            <div className="mb-5 flex items-center justify-between">
              {STEPS.map((s, i) => (
                <div key={s.key} className="flex flex-1 items-center">
                  <div className={`flex items-center gap-2 ${i <= step ? "text-primary" : "text-muted-foreground"}`}>
                    <span className={`flex h-8 w-8 items-center justify-center rounded-full border ${i < step ? "border-primary bg-primary text-primary-foreground" : i === step ? "border-primary" : "border-border"}`}>
                      {i < step ? <Check className="h-4 w-4" /> : <s.icon className="h-4 w-4" />}
                    </span>
                    <span className="hidden text-xs font-semibold sm:block">{s.label}</span>
                  </div>
                  {i < STEPS.length - 1 && <div className={`mx-1 h-0.5 flex-1 ${i < step ? "bg-primary" : "bg-border"}`} />}
                </div>
              ))}
            </div>

            {/* Step content */}
            <div className="min-h-[220px] rounded-lg border border-border/60 bg-background p-5" data-testid="demo-step">
              {step === 0 && (
                <div>
                  <div className="mb-2 flex items-center gap-2"><Radar className="h-5 w-5 text-primary" /><h3 className="font-heading text-lg font-bold">Disruption Detected</h3><LevelBadge level={data.detect.severity} /></div>
                  <p className="text-sm font-semibold">{data.detect.title}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{data.detect.description}</p>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                    <span>Location: <b className="text-foreground">{data.detect.location}</b></span>
                    <span>Type: <b className="text-foreground">{data.detect.event_type}</b></span>
                    <span>Region: <b className="text-foreground">{data.detect.affected_region}</b></span>
                    <span>Duration: <b className="text-foreground">{data.detect.estimated_duration}</b></span>
                  </div>
                </div>
              )}
              {step === 1 && (
                <div>
                  <div className="mb-2 flex items-center gap-2"><Brain className="h-5 w-5 text-primary" /><h3 className="font-heading text-lg font-bold">AI Prediction</h3></div>
                  <p className="text-sm">Highest-risk affected shipment: <b className="font-mono text-primary">{data.predict.shipment.shipment_id}</b> ({data.predict.shipment.origin} → {data.predict.shipment.destination}) <RiskBadge level={data.predict.shipment.risk_category} score={data.predict.shipment.risk_score} /></p>
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    {[["Best", data.predict.eta.best_case, "text-emerald-500"], ["Likely", data.predict.eta.most_likely, "text-primary"], ["Worst", data.predict.eta.worst_case, "text-red-500"]].map(([l, v, c]) => (
                      <div key={l} className="rounded-md border border-border/60 p-2 text-center"><p className="text-xs text-muted-foreground">{l}</p><p className={`font-mono text-sm font-bold ${c}`}>{v}</p></div>
                    ))}
                  </div>
                  <div className="mt-3"><p className="mb-1 text-xs text-muted-foreground">Confidence · delay prob {data.predict.eta.delay_probability}%</p><ConfidenceBar value={data.predict.eta.confidence} /></div>
                  <p className="mt-3 text-sm text-muted-foreground">Predicted customs clearance: <b className="text-foreground">{data.predict.customs.predicted_clearance_days}d</b> (+{data.predict.customs.expected_delay_days}d vs normal). Estimates, not guarantees.</p>
                </div>
              )}
              {step === 2 && (
                <div>
                  <div className="mb-2 flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-500" /><h3 className="font-heading text-lg font-bold">Impact Assessment</h3></div>
                  <div className="grid grid-cols-4 gap-2">
                    {[["Affected", fmtNum(data.impact.affected_count), ""], ["High", data.impact.high_risk, "text-red-500"], ["Medium", data.impact.medium_risk, "text-amber-500"], ["Low", data.impact.low_risk, "text-emerald-500"]].map(([l, v, c]) => (
                      <div key={l} className="rounded-md border border-border/60 p-2 text-center"><p className="text-xs text-muted-foreground">{l}</p><p className={`font-heading text-xl font-black ${c}`}>{v}</p></div>
                    ))}
                  </div>
                  <p className="mt-3 text-sm">Cascade projects <b>{fmtNum(data.impact.cascade.total_estimated_affected)}</b> total shipments impacted across the network. Est. exposure <b className="text-red-500">{fmtMoney(data.financial.estimated_current_exposure)}</b>, reducible to <b className="text-emerald-500">{fmtMoney(data.financial.estimated_exposure_after_recovery)}</b> after recovery.</p>
                </div>
              )}
              {step === 3 && (
                <div>
                  <div className="mb-2 flex items-center gap-2"><LifeBuoy className="h-5 w-5 text-primary" /><h3 className="font-heading text-lg font-bold">AI Recovery Recommendation</h3></div>
                  <p className="font-heading font-bold text-primary">{data.recover.action}</p>
                  <ul className="mt-2 space-y-1 text-sm text-muted-foreground">{(data.recover.reasons || []).map((r, i) => <li key={i} className="flex gap-2"><span className="text-primary">•</span>{r}</li>)}</ul>
                  <p className="mt-2 text-sm">{data.recover.explanation}</p>
                  <div className="mt-4">
                    {approved ? (
                      <div className="flex items-center gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm font-semibold text-emerald-500" data-testid="demo-approved"><Check className="h-4 w-4" /> Approved — shipment ETA updated & decision logged to audit trail.</div>
                    ) : (
                      <button data-testid="demo-approve" onClick={approve} disabled={approving} className="inline-flex items-center gap-2 rounded-md bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-600 disabled:opacity-60">{approving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Approve Recovery Plan</button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Nav */}
            <div className="mt-4 flex items-center justify-between">
              <button data-testid="demo-prev" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0} className="inline-flex items-center gap-1 rounded-md border border-border px-3 py-2 text-sm hover:bg-accent disabled:opacity-40"><ArrowLeft className="h-4 w-4" /> Back</button>
              {step < STEPS.length - 1 ? (
                <button data-testid="demo-next" onClick={() => setStep(step + 1)} className="inline-flex items-center gap-1 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90">Next <ArrowRight className="h-4 w-4" /></button>
              ) : (
                <button data-testid="demo-restart" onClick={reset} className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent">Run Again</button>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
