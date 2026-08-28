import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StateWrap, StatTile, RiskBadge, LevelBadge, fmtMoney } from "@/components/common";
import WorldMap from "@/components/WorldMap";
import GuidedDemo from "@/components/GuidedDemo";
import {
  Package, ShieldAlert, AlertTriangle, Clock, DollarSign, Radar, LifeBuoy, Timer, Play, RotateCcw, Loader2,
} from "lucide-react";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, Area, AreaChart,
} from "recharts";

const RISK_LABELS = [
  ["global", "Global"], ["port", "Port"], ["customs", "Customs"],
  ["carrier", "Carrier"], ["geopolitical", "Geopolitical"], ["weather", "Weather"],
];

function Gauge({ label, value }) {
  const tone = value >= 60 ? "#EF4444" : value >= 40 ? "#F59E0B" : "#10B981";
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border/60 bg-background p-3">
      <div className="relative h-12 w-12 shrink-0">
        <svg viewBox="0 0 36 36" className="h-12 w-12 -rotate-90">
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="hsl(var(--muted))" strokeWidth="3" />
          <circle cx="18" cy="18" r="15.9" fill="none" stroke={tone} strokeWidth="3"
            strokeDasharray={`${value} 100`} strokeLinecap="round" />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center font-mono text-xs font-bold">{Math.round(value)}</span>
      </div>
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className="text-sm font-semibold" style={{ color: tone }}>{value >= 60 ? "High" : value >= 40 ? "Moderate" : "Low"}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { canManage } = useAuth();
  const qc = useQueryClient();
  const [demoOpen, setDemoOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["dashboard"], queryFn: () => api.dashboard().then((r) => r.data) });

  const resetMut = useMutation({
    mutationFn: () => api.resetDemo(),
    onSuccess: (res) => { toast.success(`Demo reset — ${res.data.shipments} shipments re-seeded`); qc.invalidateQueries(); setResetOpen(false); },
    onError: (e) => toast.error(e.response?.data?.detail || "Reset failed"),
  });

  return (
    <>
      <PageHeader testId="dashboard-header" title="Executive Dashboard"
        subtitle="Real-time cross-border logistics resilience overview">
        {canManage() && (
          <button data-testid="reset-demo-btn" onClick={() => setResetOpen(true)}
            className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent">
            <RotateCcw className="h-4 w-4" /> Reset Demo
          </button>
        )}
        <button data-testid="run-demo-btn" onClick={() => setDemoOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5">
          <Play className="h-4 w-4" /> Run Live Demo
        </button>
      </PageHeader>
      <GuidedDemo open={demoOpen} onOpenChange={setDemoOpen} />
      <AlertDialog open={resetOpen} onOpenChange={setResetOpen}>
        <AlertDialogContent data-testid="reset-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Reset demo data?</AlertDialogTitle>
            <AlertDialogDescription>This restores a clean slate — re-seeds 126 shipments, ports, carriers, events, alerts and recommendations so you can re-run the Port of LA scenario. User accounts are kept.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction data-testid="confirm-reset" onClick={(e) => { e.preventDefault(); resetMut.mutate(); }} className="bg-primary hover:bg-primary/90">
              {resetMut.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null} Reset
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <StateWrap loading={isLoading} error={error ? "Failed to load dashboard." : null} onRetry={refetch}>
        {data && (
          <div className="space-y-6">
            {/* KPIs */}
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <StatTile testId="kpi-active" label="Active Shipments" value={data.kpis.total_active} icon={Package} />
              <StatTile testId="kpi-atrisk" label="At-Risk" value={data.kpis.at_risk} icon={ShieldAlert} tone="warning" />
              <StatTile testId="kpi-highrisk" label="High-Risk" value={data.kpis.high_risk} icon={AlertTriangle} tone="critical" />
              <StatTile testId="kpi-delays" label="Predicted Delays" value={data.kpis.predicted_delays} icon={Clock} tone="warning" />
              <StatTile testId="kpi-eta" label="Avg ETA (days)" value={data.kpis.avg_eta_days} icon={Timer} />
              <StatTile testId="kpi-cost" label="Cost Exposure" value={fmtMoney(data.kpis.cost_exposure)} icon={DollarSign} tone="critical" />
              <StatTile testId="kpi-disruptions" label="Active Disruptions" value={data.kpis.active_disruptions} icon={Radar} tone="warning" />
              <StatTile testId="kpi-recovery" label="Recovery Pending" value={data.kpis.recovery_pending} icon={LifeBuoy} />
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Map */}
              <div className="lg:col-span-2 rounded-xl border border-border/60 bg-card p-5">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="font-heading text-lg font-bold">Global Shipment & Risk Map</h2>
                  <div className="flex gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-500" />Low</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-500" />Moderate</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-orange-500" />High</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500" />Critical</span>
                  </div>
                </div>
                <WorldMap shipments={data.map_shipments} ports={data.ports} height={380} />
              </div>

              {/* Risk overview */}
              <div className="rounded-xl border border-border/60 bg-card p-5">
                <h2 className="mb-4 font-heading text-lg font-bold">Risk Overview</h2>
                <div className="mb-4 rounded-lg border border-primary/30 bg-primary/5 p-4 text-center">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">Global Risk Score</p>
                  <p className="font-heading text-4xl font-black text-primary">{Math.round(data.risk_overview.global)}<span className="text-lg text-muted-foreground">/100</span></p>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {RISK_LABELS.filter(([k]) => k !== "global").map(([k, label]) => (
                    <Gauge key={k} label={label} value={data.risk_overview[k] || 0} />
                  ))}
                </div>
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              {/* Prediction chart */}
              <div className="rounded-xl border border-border/60 bg-card p-5">
                <h2 className="mb-1 font-heading text-lg font-bold">ETA Prediction & Delay Probability</h2>
                <p className="mb-4 text-xs text-muted-foreground">Predicted vs historical ETA with confidence — estimates, not guarantees.</p>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={data.prediction_chart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" fontSize={11} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} />
                    <RTooltip contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Line type="monotone" dataKey="historical_eta" stroke="#94A3B8" strokeWidth={2} name="Historical ETA" dot={false} />
                    <Line type="monotone" dataKey="predicted_eta" stroke="#2563EB" strokeWidth={2} name="Predicted ETA" dot={false} />
                    <Line type="monotone" dataKey="delay_probability" stroke="#F59E0B" strokeWidth={2} name="Delay Prob %" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Disruption feed */}
              <div className="rounded-xl border border-border/60 bg-card p-5">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="font-heading text-lg font-bold">Live Disruption Feed</h2>
                  <span className="flex items-center gap-1.5 text-xs text-emerald-500"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500 ts-live" />Live</span>
                </div>
                <div className="space-y-3" data-testid="disruption-feed">
                  {data.disruptions.map((d) => (
                    <Link key={d.id} to="/app/geopolitical" className="block rounded-lg border border-border/60 bg-background p-3 transition-colors hover:border-primary/40">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="text-sm font-semibold">{d.title}</p>
                          <p className="mt-0.5 text-xs text-muted-foreground">{d.location} · {d.event_type}</p>
                        </div>
                        <LevelBadge level={d.severity} />
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </StateWrap>
    </>
  );
}
