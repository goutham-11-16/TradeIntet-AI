import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StateWrap, ConfidenceBar } from "@/components/common";
import { TrendingUp, TrendingDown, Minus, Check, X, Pencil, Loader2, LifeBuoy } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";

const OutcomeIcon = ({ dir }) => dir === "down" ? <TrendingDown className="h-4 w-4 text-emerald-500" /> : dir === "up" ? <TrendingUp className="h-4 w-4 text-red-500" /> : <Minus className="h-4 w-4 text-muted-foreground" />;
const STATUS_TABS = [["all", "All"], ["pending", "Pending"], ["approved", "Approved"], ["rejected", "Rejected"], ["modified", "Modified"]];

export default function Recovery() {
  const qc = useQueryClient();
  const { canManage } = useAuth();
  const [tab, setTab] = useState("pending");
  const [modal, setModal] = useState(null); // {id, action}
  const [reason, setReason] = useState("");
  const [modification, setModification] = useState("");
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["recs", tab], queryFn: () => api.recommendations(tab === "all" ? "" : tab).then((r) => r.data) });

  const decideMut = useMutation({
    mutationFn: ({ id, action, payload }) => api.decideRec(id, action, payload),
    onSuccess: (_, v) => { toast.success(`Recommendation ${v.action === "modify" ? "modified" : v.action + "d"}`); qc.invalidateQueries({ queryKey: ["recs"] }); setModal(null); setReason(""); setModification(""); },
    onError: (e) => toast.error(e.response?.data?.detail || "Action failed"),
  });

  const confirm = () => decideMut.mutate({ id: modal.id, action: modal.action, payload: { reason, modification } });

  const badge = (s) => ({ pending: "bg-amber-500/15 text-amber-500", approved: "bg-emerald-500/15 text-emerald-500", rejected: "bg-red-500/15 text-red-500", modified: "bg-blue-500/15 text-blue-500" }[s] || "");

  return (
    <>
      <PageHeader testId="recovery-header" title="Recovery Center" subtitle="Human-in-the-loop: AI recommends, managers decide" />
      <div className="flex flex-wrap gap-2" data-testid="recovery-tabs">
        {STATUS_TABS.map(([v, l]) => (
          <button key={v} data-testid={`rectab-${v}`} onClick={() => setTab(v)} className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${tab === v ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:bg-accent"}`}>{l}</button>
        ))}
      </div>

      <StateWrap loading={isLoading} error={error ? "Failed to load recommendations." : null} onRetry={refetch}
        empty={data && data.recommendations.length === 0} emptyText="No recommendations in this category.">
        <div className="grid gap-4 md:grid-cols-2" data-testid="recommendations-list">
          {data?.recommendations?.map((r) => (
            <div key={r.id} className="rounded-xl border border-border/60 bg-card p-5">
              <div className="mb-2 flex items-start justify-between gap-2">
                <div className="flex items-center gap-2"><LifeBuoy className="h-5 w-5 text-primary" /><h3 className="font-heading font-bold">{r.action}</h3></div>
                <span className={`rounded-md px-2 py-0.5 text-xs font-semibold capitalize ${badge(r.status)}`}>{r.status}</span>
              </div>
              <Link to={`/app/shipments/${r.shipment_id}`} className="font-mono text-xs text-primary hover:underline">{r.shipment_id}</Link>
              <ul className="mt-2 space-y-1 text-sm text-muted-foreground">{(r.reasons || []).map((x, i) => <li key={i} className="flex gap-2"><span className="text-primary">•</span>{x}</li>)}</ul>
              <p className="mt-2 text-sm">{r.explanation}</p>
              {r.expected_outcome && <div className="mt-3 flex gap-4 text-sm"><span className="flex items-center gap-1">ETA <OutcomeIcon dir={r.expected_outcome.eta} /></span><span className="flex items-center gap-1">Risk <OutcomeIcon dir={r.expected_outcome.risk} /></span><span className="flex items-center gap-1">Cost <OutcomeIcon dir={r.expected_outcome.cost} /></span></div>}
              <div className="mt-3"><p className="mb-1 text-xs text-muted-foreground">Confidence</p><ConfidenceBar value={r.confidence} /></div>
              {r.status === "pending" && canManage() && (
                <div className="mt-4 flex gap-2">
                  <button data-testid={`approve-${r.id}`} onClick={() => setModal({ id: r.id, action: "approve" })} className="inline-flex flex-1 items-center justify-center gap-1 rounded-md bg-emerald-500 py-2 text-sm font-semibold text-white hover:bg-emerald-600"><Check className="h-4 w-4" /> Approve</button>
                  <button data-testid={`reject-${r.id}`} onClick={() => setModal({ id: r.id, action: "reject" })} className="inline-flex flex-1 items-center justify-center gap-1 rounded-md bg-red-500 py-2 text-sm font-semibold text-white hover:bg-red-600"><X className="h-4 w-4" /> Reject</button>
                  <button data-testid={`modify-${r.id}`} onClick={() => setModal({ id: r.id, action: "modify" })} className="inline-flex items-center justify-center gap-1 rounded-md border border-border px-3 py-2 text-sm font-semibold hover:bg-accent"><Pencil className="h-4 w-4" /></button>
                </div>
              )}
              {r.status !== "pending" && r.decided_by && <p className="mt-3 text-xs text-muted-foreground">Decided by {r.decided_by}{r.decision_reason ? ` · "${r.decision_reason}"` : ""}</p>}
            </div>
          ))}
        </div>
      </StateWrap>

      <Dialog open={!!modal} onOpenChange={(o) => !o && setModal(null)}>
        <DialogContent data-testid="decision-modal">
          <DialogHeader><DialogTitle className="capitalize">{modal?.action} Recommendation</DialogTitle></DialogHeader>
          {modal?.action === "modify" && <textarea data-testid="modify-input" value={modification} onChange={(e) => setModification(e.target.value)} rows={2} placeholder="Describe your modification…" className="w-full rounded-md border border-border bg-background p-3 text-sm" />}
          <textarea data-testid="reason-input" value={reason} onChange={(e) => setReason(e.target.value)} rows={2} placeholder="Reason / notes (logged in audit trail)…" className="w-full rounded-md border border-border bg-background p-3 text-sm" />
          <DialogFooter>
            <button onClick={() => setModal(null)} className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent">Cancel</button>
            <button data-testid="confirm-decision" onClick={confirm} disabled={decideMut.isPending} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">{decideMut.isPending && <Loader2 className="h-4 w-4 animate-spin" />} Confirm</button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
