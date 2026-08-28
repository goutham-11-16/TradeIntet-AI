import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StateWrap, LevelBadge } from "@/components/common";
import { Upload, Loader2, FileText, ShieldAlert } from "lucide-react";

export default function Compliance() {
  const qc = useQueryClient();
  const { canManage } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [last, setLast] = useState(null);
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["documents"], queryFn: () => api.documents().then((r) => r.data) });

  const upload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData(); fd.append("file", file);
    try {
      const { data } = await api.compliance(fd);
      setLast(data.result);
      toast.success(`Analyzed: ${data.result.overall}`);
      qc.invalidateQueries({ queryKey: ["documents"] });
    } catch (err) { toast.error(err.response?.data?.detail || "Upload failed"); }
    finally { setUploading(false); e.target.value = ""; }
  };

  return (
    <>
      <PageHeader testId="compliance-header" title="Customs & Compliance" subtitle="Document screening & assistance — not legal certification" />
      <div className="rounded-md border border-amber-500/30 bg-amber-500/5 px-4 py-2 text-xs text-amber-500 flex items-center gap-2"><ShieldAlert className="h-4 w-4" /> This is a risk-screening and document-assistance feature. It does not provide legal compliance certification.</div>

      {canManage() && (
        <div className="rounded-xl border border-dashed border-border/60 bg-card p-8 text-center" data-testid="compliance-upload">
          <FileText className="mx-auto h-10 w-10 text-muted-foreground" />
          <p className="mt-3 text-sm font-medium">Upload commercial invoice, packing list, certificate or product document</p>
          <p className="text-xs text-muted-foreground">PDF, PNG, JPG, CSV, TXT, DOCX · max 10MB</p>
          <label data-testid="upload-doc" className="mt-4 inline-flex cursor-pointer items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90">
            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />} Upload & Analyze
            <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.csv,.txt,.docx" onChange={upload} />
          </label>
        </div>
      )}

      {last && (
        <div className="rounded-xl border border-border/60 bg-card p-5" data-testid="compliance-result">
          <div className="mb-3 flex items-center justify-between"><h2 className="font-heading text-lg font-bold">{last.filename}</h2><LevelBadge level={last.overall} /></div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div><p className="mb-2 text-xs uppercase text-muted-foreground">Field Checks</p>
              <div className="space-y-1.5">{last.checks.map((c) => (<div key={c.field} className="flex items-center justify-between text-sm"><span>{c.field}</span><LevelBadge level={c.status} /></div>))}</div>
            </div>
            <div><p className="mb-2 text-xs uppercase text-muted-foreground">Extracted Fields</p>
              <div className="space-y-1.5 text-sm">{Object.entries(last.extracted).map(([k, v]) => (<div key={k} className="flex justify-between"><span className="capitalize text-muted-foreground">{k.replace(/_/g, " ")}</span><span className="font-mono">{v}</span></div>))}</div>
            </div>
          </div>
        </div>
      )}

      <StateWrap loading={isLoading} error={error ? "Failed to load documents." : null} onRetry={refetch}
        empty={data && data.documents.length === 0} emptyText="No documents analyzed yet.">
        {data && data.documents.length > 0 && (
          <div className="rounded-xl border border-border/60 bg-card p-5">
            <h2 className="mb-3 font-heading text-lg font-bold">Document History</h2>
            <div className="overflow-x-auto"><table className="w-full text-sm" data-testid="documents-table"><thead className="border-b border-border/60 text-left text-xs uppercase text-muted-foreground"><tr><th className="px-3 py-2">File</th><th className="px-3 py-2">Result</th><th className="px-3 py-2">Uploaded By</th></tr></thead>
              <tbody>{data.documents.map((d) => (<tr key={d.id} className="border-b border-border/40"><td className="px-3 py-2">{d.filename}</td><td className="px-3 py-2"><LevelBadge level={d.overall} /></td><td className="px-3 py-2 text-muted-foreground">{d.uploaded_by}</td></tr>))}</tbody>
            </table></div>
          </div>
        )}
      </StateWrap>
    </>
  );
}
