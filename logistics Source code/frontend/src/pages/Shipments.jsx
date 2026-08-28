import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { api, API } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StateWrap, RiskBadge, StatusBadge, fmtMoney } from "@/components/common";
import {
  Plus, Download, Upload, Search, Trash2, Pencil, Eye, ArrowUpDown, Loader2,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const inputCls = "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary";
const CATS = ["Electronics", "Pharmaceuticals", "Textiles", "Automotive", "Food & Beverage", "Machinery", "Chemicals", "Consumer Goods", "Luxury"];
const METHODS = ["Sea", "Air", "Rail", "Road", "Express"];
const STATUSES = ["Preparing", "In Transit", "Customs", "Delayed", "At Risk", "Delivered", "Cancelled"];
const CARRIERS = ["Maersk Line", "MSC", "CMA CGM", "Hapag-Lloyd", "COSCO Shipping", "Evergreen Marine"];

function emptyForm() {
  return {
    origin: "", destination: "", carrier: "Maersk Line", product_category: "Consumer Goods",
    product_value: 5000, weight_kg: 500, shipping_method: "Sea", customs_status: "Pending",
    status: "Preparing", expected_delivery: "", customer_priority: "Standard",
    customer_name: "", documentation_status: "Complete", order_id: "",
  };
}

export default function Shipments() {
  const { canManage } = useAuth();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [search, setSearch] = useState(params.get("q") || "");
  const [status, setStatus] = useState("all");
  const [risk, setRisk] = useState("all");
  const [sort, setSort] = useState("risk_score");
  const [order, setOrder] = useState("desc");
  const [modal, setModal] = useState(null); // {mode, data}
  const [form, setForm] = useState(emptyForm());
  const [delId, setDelId] = useState(null);
  const [importing, setImporting] = useState(false);

  const queryStr = useMemo(() => {
    const p = new URLSearchParams();
    if (status !== "all") p.set("status", status);
    if (risk !== "all") p.set("risk", risk);
    if (search) p.set("search", search);
    p.set("sort", sort); p.set("order", order);
    return `?${p.toString()}`;
  }, [status, risk, search, sort, order]);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["shipments", queryStr], queryFn: () => api.shipments(queryStr).then((r) => r.data),
  });

  const saveMut = useMutation({
    mutationFn: (payload) => modal?.mode === "edit" ? api.updateShipment(modal.data.shipment_id, payload) : api.createShipment(payload),
    onSuccess: () => { toast.success(modal?.mode === "edit" ? "Shipment updated" : "Shipment created"); qc.invalidateQueries({ queryKey: ["shipments"] }); setModal(null); },
    onError: (e) => toast.error(e.response?.data?.detail || "Save failed"),
  });

  const delMut = useMutation({
    mutationFn: (id) => api.deleteShipment(id),
    onSuccess: () => { toast.success("Shipment deleted"); qc.invalidateQueries({ queryKey: ["shipments"] }); setDelId(null); },
    onError: (e) => toast.error(e.response?.data?.detail || "Delete failed"),
  });

  const openCreate = () => { setForm(emptyForm()); setModal({ mode: "create" }); };
  const openEdit = (s) => { setForm({ ...emptyForm(), ...s }); setModal({ mode: "edit", data: s }); };

  const submit = (e) => {
    e.preventDefault();
    if (!form.origin || !form.destination) { toast.error("Origin and destination are required"); return; }
    const { id, shipment_id, risk_score, risk_category, risk_factors, created_at, route, origin_coords, dest_coords, ...payload } = form;
    payload.product_value = Number(payload.product_value); payload.weight_kg = Number(payload.weight_kg);
    saveMut.mutate(payload);
  };

  const handleImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    const fd = new FormData(); fd.append("file", file);
    try {
      const { data } = await api.importCsv(fd);
      toast.success(`Imported ${data.imported} shipments`);
      qc.invalidateQueries({ queryKey: ["shipments"] });
    } catch (err) { toast.error(err.response?.data?.detail || "Import failed"); }
    finally { setImporting(false); e.target.value = ""; }
  };

  const toggleSort = (field) => {
    if (sort === field) setOrder(order === "desc" ? "asc" : "desc");
    else { setSort(field); setOrder("desc"); }
  };

  return (
    <>
      <PageHeader testId="shipments-header" title="Shipments" subtitle={`${data?.total ?? 0} shipments tracked`}>
        <a href={api.exportCsvUrl} data-testid="export-csv" className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-accent">
          <Download className="h-4 w-4" /> Export
        </a>
        {canManage() && (
          <>
            <label data-testid="import-csv" className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-accent">
              {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />} Import CSV
              <input type="file" accept=".csv" className="hidden" onChange={handleImport} />
            </label>
            <button data-testid="add-shipment" onClick={openCreate} className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90">
              <Plus className="h-4 w-4" /> Add Shipment
            </button>
          </>
        )}
      </PageHeader>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input data-testid="shipment-search" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search ID, route, carrier, customer…" className={`${inputCls} pl-9`} />
        </div>
        <select data-testid="filter-status" value={status} onChange={(e) => setStatus(e.target.value)} className={`${inputCls} max-w-[160px]`}>
          <option value="all">All statuses</option>
          {STATUSES.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select data-testid="filter-risk" value={risk} onChange={(e) => setRisk(e.target.value)} className={`${inputCls} max-w-[150px]`}>
          <option value="all">All risk</option>
          {["Low", "Moderate", "High", "Critical"].map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>

      <StateWrap loading={isLoading} error={error ? "Failed to load shipments." : null} onRetry={refetch}
        empty={data && data.shipments.length === 0} emptyText="No shipments match your filters.">
        {data && data.shipments.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-border/60 bg-card">
            <table className="w-full text-sm" data-testid="shipments-table">
              <thead className="border-b border-border/60 bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  {[["shipment_id", "Shipment"], ["origin", "Route"], ["carrier", "Carrier"], ["status", "Status"], ["product_value", "Value"], ["risk_score", "Risk"]].map(([f, l]) => (
                    <th key={f} className="cursor-pointer px-4 py-3 font-semibold hover:text-foreground" onClick={() => toggleSort(f)}>
                      <span className="inline-flex items-center gap-1">{l}<ArrowUpDown className="h-3 w-3" /></span>
                    </th>
                  ))}
                  <th className="px-4 py-3 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.shipments.map((s) => (
                  <tr key={s.shipment_id} className="border-b border-border/40 transition-colors hover:bg-accent/40" data-testid={`row-${s.shipment_id}`}>
                    <td className="px-4 py-3">
                      <p className="font-mono font-semibold text-primary">{s.shipment_id}</p>
                      <p className="text-xs text-muted-foreground">{s.customer_name}</p>
                    </td>
                    <td className="px-4 py-3"><p className="max-w-[200px] truncate">{s.origin} → {s.destination}</p><p className="text-xs text-muted-foreground">{s.shipping_method}</p></td>
                    <td className="px-4 py-3">{s.carrier}</td>
                    <td className="px-4 py-3"><StatusBadge status={s.status} /></td>
                    <td className="px-4 py-3 text-right font-mono">{fmtMoney(s.product_value)}</td>
                    <td className="px-4 py-3"><RiskBadge level={s.risk_category} score={s.risk_score} /></td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button data-testid={`view-${s.shipment_id}`} onClick={() => navigate(`/app/shipments/${s.shipment_id}`)} className="rounded p-1.5 hover:bg-accent" title="View"><Eye className="h-4 w-4" /></button>
                        {canManage() && <>
                          <button data-testid={`edit-${s.shipment_id}`} onClick={() => openEdit(s)} className="rounded p-1.5 hover:bg-accent" title="Edit"><Pencil className="h-4 w-4" /></button>
                          <button data-testid={`delete-${s.shipment_id}`} onClick={() => setDelId(s.shipment_id)} className="rounded p-1.5 text-red-500 hover:bg-red-500/10" title="Delete"><Trash2 className="h-4 w-4" /></button>
                        </>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </StateWrap>

      {/* Create/Edit modal */}
      <Dialog open={!!modal} onOpenChange={(o) => !o && setModal(null)}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg" data-testid="shipment-modal">
          <DialogHeader><DialogTitle>{modal?.mode === "edit" ? "Edit Shipment" : "Add Shipment"}</DialogTitle></DialogHeader>
          <form onSubmit={submit} className="grid grid-cols-2 gap-3">
            <label className="text-sm">Origin<input data-testid="f-origin" className={inputCls} value={form.origin} onChange={(e) => setForm({ ...form, origin: e.target.value })} placeholder="Port of Shanghai" /></label>
            <label className="text-sm">Destination<input data-testid="f-dest" className={inputCls} value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })} placeholder="Port of Los Angeles" /></label>
            <label className="text-sm">Carrier<select data-testid="f-carrier" className={inputCls} value={form.carrier} onChange={(e) => setForm({ ...form, carrier: e.target.value })}>{CARRIERS.map((c) => <option key={c}>{c}</option>)}</select></label>
            <label className="text-sm">Category<select data-testid="f-category" className={inputCls} value={form.product_category} onChange={(e) => setForm({ ...form, product_category: e.target.value })}>{CATS.map((c) => <option key={c}>{c}</option>)}</select></label>
            <label className="text-sm">Value ($)<input data-testid="f-value" type="number" className={inputCls} value={form.product_value} onChange={(e) => setForm({ ...form, product_value: e.target.value })} /></label>
            <label className="text-sm">Weight (kg)<input data-testid="f-weight" type="number" className={inputCls} value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: e.target.value })} /></label>
            <label className="text-sm">Method<select data-testid="f-method" className={inputCls} value={form.shipping_method} onChange={(e) => setForm({ ...form, shipping_method: e.target.value })}>{METHODS.map((m) => <option key={m}>{m}</option>)}</select></label>
            <label className="text-sm">Status<select data-testid="f-status" className={inputCls} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>{STATUSES.map((s) => <option key={s}>{s}</option>)}</select></label>
            <label className="text-sm">Priority<select data-testid="f-priority" className={inputCls} value={form.customer_priority} onChange={(e) => setForm({ ...form, customer_priority: e.target.value })}>{["Standard", "High", "Critical"].map((p) => <option key={p}>{p}</option>)}</select></label>
            <label className="text-sm">Docs<select data-testid="f-docs" className={inputCls} value={form.documentation_status} onChange={(e) => setForm({ ...form, documentation_status: e.target.value })}>{["Complete", "Incomplete", "Missing"].map((d) => <option key={d}>{d}</option>)}</select></label>
            <label className="text-sm">Customer<input data-testid="f-customer" className={inputCls} value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} placeholder="Acme Retail" /></label>
            <label className="text-sm">Expected Delivery<input data-testid="f-eta" type="date" className={inputCls} value={form.expected_delivery} onChange={(e) => setForm({ ...form, expected_delivery: e.target.value })} /></label>
            <DialogFooter className="col-span-2 mt-2">
              <button type="button" onClick={() => setModal(null)} className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent">Cancel</button>
              <button data-testid="save-shipment" disabled={saveMut.isPending} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">
                {saveMut.isPending && <Loader2 className="h-4 w-4 animate-spin" />} Save
              </button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!delId} onOpenChange={(o) => !o && setDelId(null)}>
        <AlertDialogContent data-testid="delete-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete shipment?</AlertDialogTitle>
            <AlertDialogDescription>This will permanently remove {delId}. This action cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction data-testid="confirm-delete" onClick={() => delMut.mutate(delId)} className="bg-red-500 hover:bg-red-600">Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
