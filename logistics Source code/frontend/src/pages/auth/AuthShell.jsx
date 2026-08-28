import { Link } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

const HERO = "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200";

export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="dark flex min-h-screen bg-background text-foreground">
      <div className="relative hidden w-1/2 lg:block">
        <img src={HERO} alt="Logistics" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-slate-950/75" />
        <div className="absolute inset-0 ts-grid-bg opacity-20" />
        <div className="relative flex h-full flex-col justify-between p-12">
          <Link to="/" className="flex items-center gap-3">
            <img src="/logo.svg" alt="TradeIntel AI Logo" className="h-10 w-10 object-contain rounded-md" />
            <div className="flex flex-col">
              <span className="font-heading text-xl font-extrabold text-white tracking-tight">TradeIntel AI</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-300">Business Automation Copilot</span>
            </div>
          </Link>
          <div>
            <h2 className="font-heading text-3xl font-black leading-tight text-white">Predict Disruptions.<br />Automate Workflows.<br />Recover Smarter.</h2>
            <p className="mt-4 max-w-md text-sm text-slate-300">AI-powered resilience and autonomous business automation for cross-border logistics.</p>
          </div>
        </div>
      </div>
      <div className="flex w-full items-center justify-center p-6 lg:w-1/2">
        <div className="w-full max-w-md ts-fade">
          <Link to="/" className="mb-8 flex items-center gap-2.5 lg:hidden">
            <img src="/logo.svg" alt="TradeIntel AI Logo" className="h-8 w-8 object-contain rounded-md" />
            <span className="font-heading text-lg font-extrabold">TradeIntel AI</span>
          </Link>
          <h1 className="font-heading text-2xl font-extrabold tracking-tight">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
          <div className="mt-6">{children}</div>
          {footer && <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>}
        </div>
      </div>
    </div>
  );
}

export function Field({ label, error, children }) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{label}</label>
      {children}
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}

export const inputCls =
  "w-full rounded-md border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-primary";
