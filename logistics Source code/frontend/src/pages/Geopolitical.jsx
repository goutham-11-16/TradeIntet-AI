import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StateWrap, LevelBadge } from "@/components/common";
import { Loader2, Sparkles, MapPin, Clock, Radio } from "lucide-react";

const TYPES = ["all", "Strike", "Port Closure", "Sanction", "Border Closure", "Conflict", "Regulation", "Weather", "Carrier Disruption"];

export default function Geopolitical() {
  const qc = useQueryClient();
  const { canManage } = useAuth();
  const [filter, setFilter] = useState("all");
  const [text, setText] = useState("");
  const [classifying, setClassifying] = useState(false);
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["geo"], queryFn: () => api.geoEvents().then((r) => r.data) });

  const classify = async () => {
    if (!text.trim()) { toast.error("Enter event text to classify"); return; }
    setClassifying(true);
    try {
      const { data } = await api.classifyEvent({ text });
      toast.success(`Classified as ${data.event.event_type} (${data.event.severity})`);
      setText("");
      qc.invalidateQueries({ queryKey: ["geo"] });
    } catch (e) { toast.error(e.response?.data?.detail || "Classification failed"); }
    finally { setClassifying(false); }
  };

  const events = data?.events?.filter((e) => filter === "all" || e.event_type === filter) || [];

  return (
    <>
      <PageHeader testId="geo-header" title="Geopolitical Monitor" subtitle="NLP-classified logistics risk events" />
      {canManage() && (
        <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="nlp-classifier">
          <h2 className="mb-2 font-heading text-lg font-bold flex items-center gap-2"><Sparkles className="h-5 w-5 text-primary" /> NLP Event Classifier</h2>
          <p className="mb-3 text-xs text-muted-foreground">Paste news/advisory text — the NLP layer classifies it into a structured risk event.</p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <textarea data-testid="classify-input" value={text} onChange={(e) => setText(e.target.value)} rows={2}
              placeholder="e.g. Dockworkers at the Port of Hamburg announce a 3-day strike starting Monday…"
              className="flex-1 rounded-md border border-border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-primary" />
            <button data-testid="classify-btn" onClick={classify} disabled={classifying} className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60 sm:w-40">
              {classifying ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />} Classify
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2" data-testid="geo-filters">
        {TYPES.map((t) => (
          <button key={t} data-testid={`geofilter-${t}`} onClick={() => setFilter(t)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${filter === t ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:bg-accent"}`}>
            {t === "all" ? "All Events" : t}
          </button>
        ))}
      </div>

      <StateWrap loading={isLoading} error={error ? "Failed to load events." : null} onRetry={refetch} empty={!isLoading && events.length === 0} emptyText="No events for this filter.">
        <div className="grid gap-4 md:grid-cols-2" data-testid="events-list">
          {events.map((e) => (
            <div key={e.id} className="rounded-xl border border-border/60 bg-card p-5 transition-transform hover:-translate-y-0.5">
              <div className="mb-2 flex items-start justify-between gap-2">
                <h3 className="font-heading font-bold">{e.title}</h3>
                <LevelBadge level={e.severity} />
              </div>
              <p className="mb-3 text-sm text-muted-foreground">{e.description}</p>
              <div className="grid grid-cols-2 gap-y-1.5 text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{e.location}</span>
                <span className="flex items-center gap-1"><Radio className="h-3 w-3" />{e.event_type}</span>
                <span>Region: {e.affected_region}</span>
                <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{e.estimated_duration}</span>
                <span className="col-span-2">Source: {e.source}</span>
              </div>
              <div className="mt-3 flex flex-wrap gap-1">
                {(e.affected_routes || []).map((r, i) => <span key={i} className="rounded bg-muted px-2 py-0.5 text-xs">{r}</span>)}
              </div>
            </div>
          ))}
        </div>
      </StateWrap>
    </>
  );
}
