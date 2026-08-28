import React from "react";
import { cn } from "@/lib/utils";
import { Loader2, Inbox, AlertTriangle } from "lucide-react";

export const fmtMoney = (n) =>
  n == null ? "$0" : `$${Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
export const fmtNum = (n) => (n == null ? "0" : Number(n).toLocaleString());

const RISK_STYLES = {
  Critical: "bg-red-500/15 text-red-500 border-red-500/30",
  High: "bg-orange-500/15 text-orange-500 border-orange-500/30",
  Moderate: "bg-amber-500/15 text-amber-500 border-amber-500/30",
  Low: "bg-emerald-500/15 text-emerald-500 border-emerald-500/30",
};

export function RiskBadge({ level, score, className }) {
  const s = RISK_STYLES[level] || RISK_STYLES.Low;
  return (
    <span data-testid="risk-badge" className={cn("inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-semibold", s, className)}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {level}{score != null && <span className="font-mono">{score}</span>}
    </span>
  );
}

const STATUS_STYLES = {
  Preparing: "bg-slate-500/15 text-slate-400 border-slate-500/30",
  "In Transit": "bg-blue-500/15 text-blue-400 border-blue-500/30",
  Customs: "bg-violet-500/15 text-violet-400 border-violet-500/30",
  Delayed: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  "At Risk": "bg-red-500/15 text-red-400 border-red-500/30",
  Delivered: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  Cancelled: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
};

export function StatusBadge({ status }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.Preparing;
  return <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium", s)}>{status}</span>;
}

const LEVEL_STYLES = {
  Info: "bg-sky-500/15 text-sky-400 border-sky-500/30",
  Warning: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  High: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  Critical: "bg-red-500/15 text-red-400 border-red-500/30",
  Moderate: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  Low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  Passed: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  "Review Required": "bg-amber-500/15 text-amber-400 border-amber-500/30",
  "Potential Issue": "bg-red-500/15 text-red-400 border-red-500/30",
};

export function LevelBadge({ level }) {
  const s = LEVEL_STYLES[level] || LEVEL_STYLES.Info;
  return <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold", s)}>{level}</span>;
}

export function PageHeader({ title, subtitle, children, testId }) {
  return (
    <div data-testid={testId} className="flex flex-col gap-3 border-b border-border/60 pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="font-heading text-2xl font-extrabold tracking-tight sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      {children && <div className="flex flex-wrap items-center gap-2">{children}</div>}
    </div>
  );
}

export function StateWrap({ loading, isLoading, error, empty, isEmpty, emptyText = "No data available", onRetry, children }) {
  const isCurrentlyLoading = loading || isLoading;
  const isCurrentlyEmpty = empty || isEmpty;

  if (isCurrentlyLoading)
    return (
      <div data-testid="state-loading" className="flex flex-col items-center justify-center gap-3 py-20 text-muted-foreground">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
        <p className="text-sm">Loading…</p>
      </div>
    );
  if (error)
    return (
      <div data-testid="state-error" className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <AlertTriangle className="h-8 w-8 text-red-500" />
        <p className="text-sm text-muted-foreground">{error}</p>
        {onRetry && (
          <button data-testid="state-retry" onClick={onRetry} className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent">
            Retry
          </button>
        )}
      </div>
    );
  if (isCurrentlyEmpty)
    return (
      <div data-testid="state-empty" className="flex flex-col items-center justify-center gap-3 py-20 text-muted-foreground">
        <Inbox className="h-8 w-8" />
        <p className="text-sm">{emptyText}</p>
      </div>
    );
  return children;
}

export function StatTile({ label, title, value, sub, icon: Icon, tone = "default", testId }) {
  const tones = {
    default: "text-primary bg-primary/10",
    critical: "text-red-500 bg-red-500/10",
    warning: "text-amber-500 bg-amber-500/10",
    success: "text-emerald-500 bg-emerald-500/10",
  };

  const renderIcon = () => {
    if (!Icon) return null;
    if (React.isValidElement(Icon)) return Icon;
    if (typeof Icon === "function" || typeof Icon === "object") {
      const Comp = Icon;
      return <Comp className="h-4 w-4" />;
    }
    return null;
  };

  return (
    <div data-testid={testId} className="group rounded-lg border border-border/60 bg-card p-5 transition-transform hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label || title}</p>
        {Icon && <span className={cn("rounded-md p-2 flex items-center justify-center", tones[tone])}>{renderIcon()}</span>}
      </div>
      <p className="mt-3 font-heading text-3xl font-extrabold tracking-tight">{value}</p>
      {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
    </div>
  );
}

export function ConfidenceBar({ value }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${value}%` }} />
      </div>
      <span className="font-mono text-xs font-semibold">{value}%</span>
    </div>
  );
}
