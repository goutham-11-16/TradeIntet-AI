import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StateWrap, LevelBadge } from "@/components/common";
import { Check, Archive, CheckCheck, Bell, Mail } from "lucide-react";

const LEVELS = ["all", "Info", "Warning", "High", "Critical"];

export default function Alerts() {
  const qc = useQueryClient();
  const { canManage } = useAuth();
  const [level, setLevel] = useState("all");
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [notifyingId, setNotifyingId] = useState(null);
  const params = `?${level !== "all" ? `level=${level}&` : ""}${unreadOnly ? "unread=true" : ""}`;
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["alerts", params], queryFn: () => api.alerts(params).then((r) => r.data) });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["alerts"] });
  const readMut = useMutation({ mutationFn: (id) => api.readAlert(id), onSuccess: invalidate });
  const archiveMut = useMutation({ mutationFn: (id) => api.archiveAlert(id), onSuccess: invalidate });
  const readAllMut = useMutation({ mutationFn: () => api.readAllAlerts(), onSuccess: () => { toast.success("All marked read"); invalidate(); } });

  const notify = async (id) => {
    setNotifyingId(id);
    try { const { data } = await api.notifyAlert(id); toast.success(`Emailed to ${data.recipient}`); }
    catch (e) { toast.error(e.response?.data?.detail || "Email failed"); }
    finally { setNotifyingId(null); }
  };

  return (
    <>
      <PageHeader testId="alerts-header" title="Alerts" subtitle={`${data?.unread_count ?? 0} unread notifications`}>
        <button data-testid="read-all" onClick={() => readAllMut.mutate()} className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-accent"><CheckCheck className="h-4 w-4" /> Mark all read</button>
      </PageHeader>

      <div className="flex flex-wrap items-center gap-2" data-testid="alert-filters">
        {LEVELS.map((l) => (
          <button key={l} data-testid={`alertfilter-${l}`} onClick={() => setLevel(l)} className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${level === l ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:bg-accent"}`}>{l === "all" ? "All" : l}</button>
        ))}
        <label className="ml-2 flex items-center gap-2 text-xs text-muted-foreground"><input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} data-testid="unread-toggle" className="h-4 w-4" /> Unread only</label>
      </div>

      <StateWrap loading={isLoading} error={error ? "Failed to load alerts." : null} onRetry={refetch}
        empty={data && data.alerts.length === 0} emptyText="No alerts to show.">
        <div className="space-y-2" data-testid="alerts-list">
          {data?.alerts?.map((a) => (
            <div key={a.id} className={`flex items-center gap-3 rounded-lg border p-4 ${a.read ? "border-border/60 bg-card" : "border-primary/30 bg-primary/5"}`} data-testid={`alert-${a.id}`}>
              <Bell className={`h-5 w-5 shrink-0 ${a.read ? "text-muted-foreground" : "text-primary"}`} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2"><p className="truncate text-sm font-semibold">{a.title}</p><LevelBadge level={a.level} /></div>
                <p className="truncate text-xs text-muted-foreground">{a.message}</p>
              </div>
              {a.shipment_id && <Link to={`/app/shipments/${a.shipment_id}`} className="hidden text-xs font-semibold text-primary hover:underline sm:block">View shipment</Link>}
              {canManage() && (a.level === "High" || a.level === "Critical") && (
                <button data-testid={`notify-${a.id}`} onClick={() => notify(a.id)} disabled={notifyingId === a.id} className="rounded p-1.5 text-primary hover:bg-primary/10 disabled:opacity-50" title="Email this alert to manager"><Mail className="h-4 w-4" /></button>
              )}
              {!a.read && <button data-testid={`read-${a.id}`} onClick={() => readMut.mutate(a.id)} className="rounded p-1.5 hover:bg-accent" title="Mark read"><Check className="h-4 w-4" /></button>}
              <button data-testid={`archive-${a.id}`} onClick={() => archiveMut.mutate(a.id)} className="rounded p-1.5 hover:bg-accent" title="Archive"><Archive className="h-4 w-4" /></button>
            </div>
          ))}
        </div>
      </StateWrap>
    </>
  );
}
