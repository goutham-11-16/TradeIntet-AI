import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader, StateWrap } from "@/components/common";
import { FileText, Download, FileDown } from "lucide-react";

const REPORTS = [
  ["shipment-risk", "Shipment Risk Report", "Highest-risk shipments with scores"],
  ["disruption", "Disruption Report", "Active geopolitical & logistics events"],
  ["cost-impact", "Cost Impact Report", "Value exposure by product category"],
  ["carrier-performance", "Carrier Performance Report", "On-time, delays & risk by carrier"],
  ["customs", "Customs Report", "Customs & documentation status"],
  ["executive-summary", "Executive Summary", "High-level KPIs for leadership"],
];

export default function Reports() {
  const [active, setActive] = useState("shipment-risk");
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["report", active], queryFn: () => api.report(active).then((r) => r.data) });

  return (
    <>
      <PageHeader testId="reports-header" title="Reports" subtitle="Generate, view and export operational reports" />
      <div className="grid gap-6 lg:grid-cols-4">
        <div className="space-y-2 lg:col-span-1" data-testid="report-list">
          {REPORTS.map(([id, name, desc]) => (
            <button key={id} data-testid={`report-${id}`} onClick={() => setActive(id)}
              className={`w-full rounded-lg border p-3 text-left transition-colors ${active === id ? "border-primary bg-primary/10" : "border-border/60 bg-card hover:bg-accent"}`}>
              <p className="flex items-center gap-2 text-sm font-semibold"><FileText className="h-4 w-4 text-primary" />{name}</p>
              <p className="mt-1 text-xs text-muted-foreground">{desc}</p>
            </button>
          ))}
        </div>

        <div className="rounded-xl border border-border/60 bg-card p-5 lg:col-span-3">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-heading text-lg font-bold">{REPORTS.find(([id]) => id === active)?.[1]}</h2>
            <a href={api.reportExportUrl(active)} data-testid="export-report" className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-accent"><Download className="h-4 w-4" /> Export CSV</a>
            <a href={api.reportPdfUrl(active)} data-testid="export-pdf" className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"><FileDown className="h-4 w-4" /> Export PDF</a>
          </div>
          <StateWrap loading={isLoading} error={error ? "Failed to generate report." : null} onRetry={refetch} empty={data && data.rows.length === 0} emptyText="No data for this report.">
            {data && data.rows.length > 0 && (
              <>
                <p className="mb-3 text-xs text-muted-foreground">Generated {new Date(data.generated_at).toLocaleString()} · {data.count} rows</p>
                <div className="overflow-x-auto"><table className="w-full text-sm" data-testid="report-table">
                  <thead className="border-b border-border/60 text-left text-xs uppercase text-muted-foreground"><tr>{Object.keys(data.rows[0]).map((k) => <th key={k} className="px-3 py-2 font-semibold">{k}</th>)}</tr></thead>
                  <tbody>{data.rows.map((row, i) => (<tr key={i} className="border-b border-border/40 hover:bg-accent/40">{Object.values(row).map((v, j) => <td key={j} className="px-3 py-2">{String(v)}</td>)}</tr>))}</tbody>
                </table></div>
              </>
            )}
          </StateWrap>
        </div>
      </div>
    </>
  );
}
