import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader, RiskBadge, ConfidenceBar } from "@/components/common";
import { Loader2, FileSearch } from "lucide-react";

const inputCls = "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary";
const COUNTRIES = ["USA", "China", "India", "Germany", "UK", "Netherlands", "UAE", "Singapore", "Brazil", "Japan", "Australia", "France", "Canada"];
const CATS = ["Electronics", "Pharmaceuticals", "Textiles", "Automotive", "Food & Beverage", "Machinery", "Chemicals", "Consumer Goods", "Luxury"];

export default function CustomsIntelligence() {
  const [form, setForm] = useState({
    destination_country: "USA", product_category: "Electronics", shipment_value: 25000,
    current_congestion: 60, season: "Peak", documentation_status: "Complete",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const predict = async () => {
    setLoading(true);
    try {
      const { data } = await api.predictCustoms({ ...form, shipment_value: Number(form.shipment_value), current_congestion: Number(form.current_congestion) });
      setResult(data);
    } catch (e) { toast.error("Prediction failed"); }
    finally { setLoading(false); }
  };

  return (
    <>
      <PageHeader testId="customs-header" title="Customs Intelligence" subtitle="AI-powered customs clearance delay prediction" />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="customs-form">
          <h2 className="mb-4 font-heading text-lg font-bold flex items-center gap-2"><FileSearch className="h-5 w-5 text-primary" /> Prediction Inputs</h2>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm">Destination<select data-testid="c-country" className={inputCls} value={form.destination_country} onChange={set("destination_country")}>{COUNTRIES.map((c) => <option key={c}>{c}</option>)}</select></label>
            <label className="text-sm">Category<select data-testid="c-category" className={inputCls} value={form.product_category} onChange={set("product_category")}>{CATS.map((c) => <option key={c}>{c}</option>)}</select></label>
            <label className="text-sm">Value ($)<input data-testid="c-value" type="number" className={inputCls} value={form.shipment_value} onChange={set("shipment_value")} /></label>
            <label className="text-sm">Congestion (%)<input data-testid="c-congestion" type="number" className={inputCls} value={form.current_congestion} onChange={set("current_congestion")} /></label>
            <label className="text-sm">Season<select data-testid="c-season" className={inputCls} value={form.season} onChange={set("season")}>{["Normal", "Peak", "Holiday", "Off-Peak"].map((s) => <option key={s}>{s}</option>)}</select></label>
            <label className="text-sm">Documentation<select data-testid="c-docs" className={inputCls} value={form.documentation_status} onChange={set("documentation_status")}>{["Complete", "Incomplete", "Missing"].map((s) => <option key={s}>{s}</option>)}</select></label>
          </div>
          <button data-testid="predict-customs" onClick={predict} disabled={loading} className="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />} Predict Clearance
          </button>
        </div>

        <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="customs-result">
          <h2 className="mb-4 font-heading text-lg font-bold">Prediction Result</h2>
          {result ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg border border-border/60 bg-background p-4 text-center"><p className="text-xs text-muted-foreground">Predicted</p><p className="font-heading text-2xl font-black text-primary">{result.predicted_clearance_days}<span className="text-sm">d</span></p></div>
                <div className="rounded-lg border border-border/60 bg-background p-4 text-center"><p className="text-xs text-muted-foreground">Normal</p><p className="font-heading text-2xl font-black">{result.normal_clearance_days}<span className="text-sm">d</span></p></div>
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-center"><p className="text-xs text-muted-foreground">Extra Delay</p><p className="font-heading text-2xl font-black text-amber-500">+{result.expected_delay_days}<span className="text-sm">d</span></p></div>
              </div>
              <div className="rounded-lg border border-border/60 bg-background p-4">
                <p className="mb-1 flex justify-between text-sm"><span className="text-muted-foreground">Delay probability</span><span className="font-mono font-bold text-amber-500">{result.delay_probability}%</span></p>
                <p className="mb-1 text-xs text-muted-foreground">Confidence</p><ConfidenceBar value={result.confidence} />
                <p className="mt-3 flex items-center justify-between text-sm">Risk category <RiskBadge level={result.risk_category === "High" ? "High" : result.risk_category === "Moderate" ? "Moderate" : "Low"} /></p>
              </div>
              <div className="rounded-lg border border-border/60 bg-background p-4">
                <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Key Drivers</p>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between"><span>Congestion impact</span><span className="font-mono">+{result.drivers.congestion_days}d</span></div>
                  <div className="flex justify-between"><span>Documentation penalty</span><span className="font-mono">+{result.drivers.documentation_penalty}d</span></div>
                  <div className="flex justify-between"><span>Category multiplier</span><span className="font-mono">×{result.drivers.category_multiplier}</span></div>
                  <div className="flex justify-between"><span>Season multiplier</span><span className="font-mono">×{result.drivers.season_multiplier}</span></div>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">Statistical model on seeded historical data. Estimates only — not a guarantee.</p>
            </div>
          ) : <p className="py-16 text-center text-sm text-muted-foreground">Enter inputs and run a prediction to see results.</p>}
        </div>
      </div>
    </>
  );
}
