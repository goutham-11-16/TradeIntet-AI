import { Link } from "react-router-dom";
import {
  ShieldCheck, Radar, Brain, Route as RouteIcon, LifeBuoy, Activity, Globe2,
  TrendingDown, Clock, ArrowRight, Ship, AlertTriangle, CheckCircle2,
} from "lucide-react";

const HERO_IMG = "https://images.unsplash.com/photo-1613690399151-65ea69478674?crop=entropy&cs=srgb&fm=jpg&q=85&w=1920";

const STEPS = [
  { icon: Radar, label: "Monitor" }, { icon: Brain, label: "Predict" },
  { icon: AlertTriangle, label: "Assess" }, { icon: RouteIcon, label: "Optimize" },
  { icon: LifeBuoy, label: "Recover" },
];

const FEATURES = [
  { icon: Brain, title: "AI Customs & ETA Prediction", desc: "Forecast clearance times and delivery windows with confidence scores from historical patterns." },
  { icon: Globe2, title: "Geopolitical Risk Monitor", desc: "NLP-classified events — strikes, closures, sanctions, weather — mapped to your routes." },
  { icon: Radar, title: "Impact & Cascade Analysis", desc: "Instantly identify affected shipments and model secondary and tertiary disruption effects." },
  { icon: RouteIcon, title: "Weighted Route Optimizer", desc: "Compare alternatives on cost, ETA, risk and resilience with configurable priorities." },
  { icon: LifeBuoy, title: "Explainable Recovery Engine", desc: "AI recommendations with reasons — approved by a human before any action is taken." },
  { icon: Activity, title: "Real-Time Alert Engine", desc: "Info to Critical alerts when risk rises, ETAs shift, or compliance issues surface." },
];

const BENEFITS = [
  { icon: Clock, title: "Reduced Delays", desc: "Anticipate bottlenecks before they cascade." },
  { icon: TrendingDown, title: "Lower Risk Exposure", desc: "Unified risk scoring across every corridor." },
  { icon: RouteIcon, title: "Smarter Routing", desc: "Resilient alternatives, not just cheapest lanes." },
  { icon: LifeBuoy, title: "Faster Recovery", desc: "Guided playbooks with human approval." },
];

function Nav() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 glass border-b border-border/60">
      <div className="mx-auto flex h-16 max-w-7xl items-center px-6">
        <Link to="/" className="flex items-center gap-2.5" data-testid="landing-logo">
          <img src="/logo.svg" alt="TradeIntel AI Logo" className="h-8 w-8 object-contain rounded-md" />
          <span className="font-heading text-lg font-extrabold bg-gradient-to-r from-primary via-blue-400 to-indigo-400 bg-clip-text text-transparent">TradeIntel AI</span>
        </Link>
        <nav className="ml-10 hidden gap-6 text-sm text-muted-foreground md:flex">
          <a href="#features" className="hover:text-foreground">Features</a>
          <a href="#how" className="hover:text-foreground">How It Works</a>
          <a href="#benefits" className="hover:text-foreground">Benefits</a>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Link to="/login" data-testid="nav-login" className="rounded-md px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground">Sign in</Link>
          <Link to="/register" data-testid="nav-getstarted" className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90">Get Started</Link>
        </div>
      </div>
    </header>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground dark">
      <Nav />

      {/* Hero */}
      <section className="relative flex min-h-screen items-center overflow-hidden pt-16">
        <img src={HERO_IMG} alt="Global cargo shipping" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-slate-950/80" />
        <div className="absolute inset-0 ts-grid-bg opacity-20" />
        <div className="relative mx-auto grid max-w-7xl gap-10 px-6 py-20 lg:grid-cols-2 lg:items-center">
          <div className="ts-fade">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-primary">
              <Ship className="h-3.5 w-3.5" /> Cross-Border Logistics Resilience
            </span>
            <h1 className="mt-6 font-heading text-4xl font-black leading-[1.05] tracking-tight text-white sm:text-5xl lg:text-6xl">
              Predict Disruptions.<br />Protect Trade.<br /><span className="text-primary">Recover Smarter.</span>
            </h1>
            <p className="mt-6 max-w-lg text-base leading-relaxed text-slate-300">
              TradeIntel AI detects international logistics disruptions, predicts their impact,
              pinpoints affected shipments, and orchestrates autonomous business automation workflows — with a human always in the loop.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/register" data-testid="hero-getstarted" className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5">
                Get Started <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/login" data-testid="hero-viewdemo" className="inline-flex items-center gap-2 rounded-md border border-white/25 bg-white/5 px-6 py-3 text-sm font-semibold text-white backdrop-blur transition-colors hover:bg-white/10">
                View Demo
              </Link>
            </div>
            <p className="mt-4 text-xs text-slate-400 font-medium">Demo: <span className="text-white font-mono">admin</span> · <span className="text-white font-mono">admin123</span></p>
          </div>
          <div className="ts-fade rounded-xl border border-white/10 bg-slate-900/70 p-5 backdrop-blur-xl" style={{ animationDelay: "0.15s" }}>
            <div className="mb-4 flex items-center justify-between">
              <p className="font-heading text-sm font-bold text-white">Live Risk Overview</p>
              <span className="flex items-center gap-1.5 text-xs text-emerald-400"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400 ts-live" /> Monitoring</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[["Active Shipments", "106", "text-white"], ["High Risk", "24", "text-red-400"], ["Disruptions", "8", "text-orange-400"], ["Avg Confidence", "84%", "text-primary"]].map(([l, v, c]) => (
                <div key={l} className="rounded-lg border border-white/10 bg-white/5 p-4">
                  <p className="text-[11px] uppercase tracking-wide text-slate-400">{l}</p>
                  <p className={`mt-1 font-heading text-2xl font-extrabold ${c}`}>{v}</p>
                </div>
              ))}
            </div>
            <div className="mt-4 space-y-2">
              {[["Port of Los Angeles Strike", "Critical"], ["Red Sea Lane Disruption", "High"], ["Shanghai Congestion", "High"]].map(([e, s]) => (
                <div key={e} className="flex items-center justify-between rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200">
                  <span className="truncate">{e}</span>
                  <span className={`ml-2 shrink-0 rounded px-2 py-0.5 text-xs font-semibold ${s === "Critical" ? "bg-red-500/20 text-red-300" : "bg-orange-500/20 text-orange-300"}`}>{s}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="border-y border-border/60 bg-card py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-primary">The Problem</p>
          <h2 className="mt-3 font-heading text-3xl font-extrabold tracking-tight">Cross-border logistics is full of blind spots</h2>
          <p className="mt-4 text-muted-foreground">
            Port strikes, customs backlogs, geopolitical events and weather cascade through supply chains
            faster than teams can react. By the time a delay surfaces in a spreadsheet, the damage is already
            spreading to dozens of downstream shipments and customers.
          </p>
        </div>
      </section>

      {/* Solution / Steps */}
      <section id="how" className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center">
            <p className="text-xs font-semibold uppercase tracking-widest text-primary">How It Works</p>
            <h2 className="mt-3 font-heading text-3xl font-extrabold tracking-tight">Monitor → Predict → Assess → Optimize → Recover</h2>
          </div>
          <div className="mt-12 flex flex-col items-center justify-between gap-4 md:flex-row">
            {STEPS.map((s, i) => (
              <div key={s.label} className="flex flex-1 flex-col items-center">
                <div className="flex items-center gap-3">
                  <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 text-primary"><s.icon className="h-6 w-6" /></div>
                  {i < STEPS.length - 1 && <ArrowRight className="hidden h-5 w-5 text-muted-foreground md:block" />}
                </div>
                <p className="mt-3 font-heading font-bold">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-border/60 bg-card py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center">
            <p className="text-xs font-semibold uppercase tracking-widest text-primary">Capabilities</p>
            <h2 className="mt-3 font-heading text-3xl font-extrabold tracking-tight">Everything you need to stay ahead</h2>
          </div>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="group rounded-xl border border-border/60 bg-background p-6 transition-transform hover:-translate-y-1">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary"><f.icon className="h-5 w-5" /></div>
                <h3 className="mt-4 font-heading text-lg font-bold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section id="benefits" className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {BENEFITS.map((b) => (
              <div key={b.title} className="rounded-xl border border-border/60 bg-card p-6">
                <b.icon className="h-6 w-6 text-primary" />
                <h3 className="mt-4 font-heading font-bold">{b.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{b.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border/60 bg-primary py-16 text-primary-foreground">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="font-heading text-3xl font-black tracking-tight">Start Protecting Your Global Shipments</h2>
          <p className="mt-3 opacity-90">Join logistics teams building resilient, disruption-ready supply chains.</p>
          <Link to="/register" data-testid="cta-getstarted" className="mt-8 inline-flex items-center gap-2 rounded-md bg-white px-7 py-3 text-sm font-bold text-primary transition-transform hover:-translate-y-0.5">
            Get Started Free <ArrowRight className="h-4 w-4" />
          </Link>
          <p className="mt-6 flex items-center justify-center gap-2 text-xs opacity-80"><CheckCircle2 className="h-4 w-4" /> Predictions include confidence scores and are estimates, not guarantees.</p>
        </div>
      </section>

      <footer className="border-t border-border/60 bg-card py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-6 text-sm text-muted-foreground sm:flex-row">
          <div className="flex items-center gap-2.5">
            <img src="/logo.svg" alt="TradeIntel AI Logo" className="h-5 w-5 object-contain" />
            <span className="font-semibold text-foreground">TradeIntel AI</span> © 2026
          </div>
          <p>AI-Powered Autonomous Business Automation & Logistics Platform</p>
        </div>
      </footer>
    </div>
  );
}
