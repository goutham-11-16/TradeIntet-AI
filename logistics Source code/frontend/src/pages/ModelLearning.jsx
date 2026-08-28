import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader, StateWrap } from "@/components/common";
import { Brain, Target, Gauge, TrendingUp } from "lucide-react";
import {
  ResponsiveContainer, ComposedChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip as RTooltip, Legend, Cell,
} from "recharts";

const tip = { background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 };
const BUCKET_COLORS = { "0-1d": "#10B981", "1-2d": "#F59E0B", "2-3d": "#F97316", ">3d": "#EF4444" };

export default function ModelLearning() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["performance"], queryFn: () => api.predictionPerformance().then((r) => r.data) });

  return (
    <>
      <PageHeader testId="model-header" title="Model Learning"
        subtitle="Predicted vs actual ETAs — continuous learning & accuracy over time" />
      <StateWrap loading={isLoading} error={error ? "Failed to load model performance." : null} onRetry={refetch}
        empty={data && data.count === 0} emptyText="No prediction feedback recorded yet.">
        {data && data.count > 0 && (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="metric-accuracy">
                <div className="flex items-center justify-between"><p className="text-xs uppercase text-muted-foreground">Model Accuracy</p><span className="rounded-md bg-emerald-500/10 p-2 text-emerald-500"><Target className="h-4 w-4" /></span></div>
                <p className="mt-2 font-heading text-3xl font-black text-emerald-500">{data.accuracy_pct}%</p>
              </div>
              <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="metric-mae">
                <div className="flex items-center justify-between"><p className="text-xs uppercase text-muted-foreground">Mean Abs. Error</p><span className="rounded-md bg-primary/10 p-2 text-primary"><Gauge className="h-4 w-4" /></span></div>
                <p className="mt-2 font-heading text-3xl font-black">{data.mae}d</p>
              </div>
              <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="metric-within1">
                <div className="flex items-center justify-between"><p className="text-xs uppercase text-muted-foreground">Within ±1 Day</p><span className="rounded-md bg-primary/10 p-2 text-primary"><TrendingUp className="h-4 w-4" /></span></div>
                <p className="mt-2 font-heading text-3xl font-black">{data.within_1_day_pct}%</p>
                <p className="mt-1 text-xs text-muted-foreground">across {data.count} tracked shipments</p>
              </div>
            </div>

            <div className="rounded-xl border border-border/60 bg-card p-5">
              <h2 className="font-heading text-lg font-bold flex items-center gap-2"><Brain className="h-5 w-5 text-primary" /> Predicted vs Actual ETA</h2>
              <p className="mb-3 text-xs text-muted-foreground">Per tracked shipment (delivered). Closer lines = better predictions. Estimates, not guarantees.</p>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={data.series}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="label" stroke="hsl(var(--muted-foreground))" fontSize={9} interval={Math.max(0, Math.floor(data.series.length / 12))} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} label={{ value: "days", angle: -90, position: "insideLeft", fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <RTooltip contentStyle={tip} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="predicted" stroke="#2563EB" strokeWidth={2} name="Predicted ETA" dot={{ r: 2 }} />
                  <Line type="monotone" dataKey="actual" stroke="#F59E0B" strokeWidth={2} name="Actual ETA" dot={{ r: 2 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-border/60 bg-card p-5">
                <h2 className="mb-3 font-heading text-lg font-bold">Prediction Error Distribution</h2>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.error_buckets}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="range" stroke="hsl(var(--muted-foreground))" fontSize={11} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} allowDecimals={false} />
                    <RTooltip contentStyle={tip} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {data.error_buckets.map((b) => <Cell key={b.range} fill={BUCKET_COLORS[b.range] || "#2563EB"} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="rounded-xl border border-border/60 bg-card p-5">
                <h2 className="mb-3 font-heading text-lg font-bold">Recent Predictions</h2>
                <div className="max-h-60 overflow-auto">
                  <table className="w-full text-sm" data-testid="predictions-table">
                    <thead className="sticky top-0 border-b border-border/60 bg-card text-left text-xs uppercase text-muted-foreground"><tr><th className="px-3 py-2">Shipment</th><th className="px-3 py-2">Predicted</th><th className="px-3 py-2">Actual</th><th className="px-3 py-2">Error</th></tr></thead>
                    <tbody>{data.predictions.map((p) => (
                      <tr key={p.id} className="border-b border-border/40"><td className="px-3 py-2 font-mono">{p.shipment_id}</td><td className="px-3 py-2 font-mono">{p.predicted_eta_days}d</td><td className="px-3 py-2 font-mono">{p.actual_eta_days}d</td><td className={`px-3 py-2 font-mono ${p.error_days <= 1 ? "text-emerald-500" : p.error_days <= 3 ? "text-amber-500" : "text-red-500"}`}>±{p.error_days}d</td></tr>
                    ))}</tbody>
                  </table>
                </div>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">Feedback loop: as shipments complete, actual ETAs are recorded against predictions to measure and improve model accuracy. This pipeline is ready for retraining on accumulated data.</p>
          </div>
        )}
      </StateWrap>
    </>
  );
}
