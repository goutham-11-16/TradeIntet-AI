import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader, StateWrap, fmtMoney } from "@/components/common";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend,
} from "recharts";

const COLORS = ["#2563EB", "#10B981", "#F59E0B", "#F97316", "#EF4444", "#0EA5E9", "#8B5CF6", "#14B8A6", "#EC4899"];
const tip = { background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 };

function Card({ title, children, sub }) {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-5">
      <h2 className="font-heading text-lg font-bold">{title}</h2>
      {sub && <p className="mb-3 text-xs text-muted-foreground">{sub}</p>}
      <div className={sub ? "" : "mt-3"}>{children}</div>
    </div>
  );
}

export default function Analytics() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["analytics"], queryFn: () => api.analytics().then((r) => r.data) });

  return (
    <>
      <PageHeader testId="analytics-header" title="Analytics" subtitle="Trends, performance & model effectiveness from live data" />
      <StateWrap loading={isLoading} error={error ? "Failed to load analytics." : null} onRetry={refetch}>
        {data && (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-border/60 bg-card p-5"><p className="text-xs uppercase text-muted-foreground">Model Accuracy</p><p className="font-heading text-3xl font-black text-emerald-500">{data.model_performance.accuracy_pct}%</p></div>
              <div className="rounded-xl border border-border/60 bg-card p-5"><p className="text-xs uppercase text-muted-foreground">Avg Prediction Error</p><p className="font-heading text-3xl font-black">{data.model_performance.avg_error_days}d</p></div>
              <div className="rounded-xl border border-border/60 bg-card p-5"><p className="text-xs uppercase text-muted-foreground">Tracked Predictions</p><p className="font-heading text-3xl font-black">{data.model_performance.predictions}</p></div>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card title="Delay Trend" sub="Average delay days per week">
                <ResponsiveContainer width="100%" height={240}><LineChart data={data.delay_trend}><CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" /><XAxis dataKey="week" stroke="hsl(var(--muted-foreground))" fontSize={11} /><YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} /><RTooltip contentStyle={tip} /><Line type="monotone" dataKey="avg_delay" stroke="#2563EB" strokeWidth={2} name="Avg delay (d)" /></LineChart></ResponsiveContainer>
              </Card>
              <Card title="Carrier Performance" sub="On-time % by carrier">
                <ResponsiveContainer width="100%" height={240}><BarChart data={data.carrier_performance}><CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" /><XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={9} interval={0} angle={-15} textAnchor="end" height={50} /><YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} /><RTooltip contentStyle={tip} /><Bar dataKey="on_time" fill="#10B981" name="On-time %" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer>
              </Card>
              <Card title="Risk Distribution" sub="Shipments by risk category">
                <ResponsiveContainer width="100%" height={240}><PieChart><Pie data={data.risk_distribution} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>{data.risk_distribution.map((e, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><RTooltip contentStyle={tip} /><Legend wrapperStyle={{ fontSize: 12 }} /></PieChart></ResponsiveContainer>
              </Card>
              <Card title="Status Distribution" sub="Shipments by status">
                <ResponsiveContainer width="100%" height={240}><PieChart><Pie data={data.status_distribution} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={45} outerRadius={80}>{data.status_distribution.map((e, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><RTooltip contentStyle={tip} /><Legend wrapperStyle={{ fontSize: 12 }} /></PieChart></ResponsiveContainer>
              </Card>
              <Card title="Cost Exposure by Category" sub="Total product value">
                <ResponsiveContainer width="100%" height={240}><BarChart data={data.cost_by_category} layout="vertical"><CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" /><XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={10} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} /><YAxis type="category" dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} width={110} /><RTooltip contentStyle={tip} formatter={(v) => fmtMoney(v)} /><Bar dataKey="value" fill="#2563EB" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer>
              </Card>
              <Card title="Disruption Frequency" sub="Events by type">
                <ResponsiveContainer width="100%" height={240}><BarChart data={data.disruption_frequency}><CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" /><XAxis dataKey="type" stroke="hsl(var(--muted-foreground))" fontSize={9} interval={0} angle={-15} textAnchor="end" height={50} /><YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} /><RTooltip contentStyle={tip} /><Bar dataKey="count" fill="#F59E0B" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer>
              </Card>
            </div>
          </div>
        )}
      </StateWrap>
    </>
  );
}
