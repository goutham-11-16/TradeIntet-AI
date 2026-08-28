import { useState, useEffect } from "react";
import { NavLink, useNavigate, Link } from "react-router-dom";
import { useTheme } from "next-themes";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Package, ShieldAlert, FileCheck2, Globe2, Radar, FlaskConical,
  Route, LifeBuoy, ClipboardCheck, BarChart3, FileText, Bell, Plug, Settings,
  Search, Sun, Moon, LogOut, Menu, X, ChevronDown, ShieldCheck, Brain,
  Bot, Workflow, Lightbulb, AlertTriangle, Activity,
} from "lucide-react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const NAV = [
  { to: "/app/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/app/shipments", label: "Shipments", icon: Package },
  { to: "/app/risk", label: "Risk Intelligence", icon: ShieldAlert },
  { to: "/app/customs", label: "Customs Intelligence", icon: FileCheck2 },
  { to: "/app/geopolitical", label: "Geopolitical Monitor", icon: Globe2 },
  { to: "/app/impact", label: "Impact Analysis", icon: Radar },
  { to: "/app/simulator", label: "What-If Simulator", icon: FlaskConical },
  { to: "/app/routes", label: "Route Optimizer", icon: Route },
  { to: "/app/recovery", label: "Recovery Center", icon: LifeBuoy },
  { to: "/app/compliance", label: "Compliance", icon: ClipboardCheck },
  { to: "/app/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/app/model-learning", label: "Model Learning", icon: Brain },
  { to: "/app/reports", label: "Reports", icon: FileText },
  { to: "/app/alerts", label: "Alerts", icon: Bell },
  { to: "/app/integrations", label: "Integrations", icon: Plug },
  { to: "/app/settings", label: "Settings", icon: Settings },
  // ─── AI Business Automation ─────────────────────────
  { divider: true, label: "AI Automation" },
  { to: "/app/copilot", label: "Automation Copilot", icon: Bot },
  { to: "/app/workflows", label: "Workflow Studio", icon: Workflow },
  { to: "/app/opportunities", label: "Opportunities", icon: Lightbulb },
  { to: "/app/conflicts", label: "Conflict Center", icon: AlertTriangle },
  { to: "/app/automation-insights", label: "Automation Insights", icon: Activity },
];

export default function DashboardLayout({ children }) {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [unread, setUnread] = useState(0);
  const [org] = useState(user?.organization || "TradeIntel AI");

  useEffect(() => {
    api.alerts("?unread=true").then(({ data }) => setUnread(data.unread_count || 0)).catch(() => {});
  }, []);

  const doSearch = (e) => {
    e.preventDefault();
    if (search.trim()) navigate(`/app/shipments?q=${encodeURIComponent(search.trim())}`);
  };

  const initials = (user?.name || "U").split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-40 w-64 transform border-r border-border/60 bg-card transition-transform duration-200 lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-16 items-center gap-2.5 border-b border-border/60 px-5">
          <img src="/logo.svg" alt="TradeIntel AI Logo" className="h-8 w-8 object-contain rounded-md" />
          <div className="flex flex-col">
            <span className="font-heading text-base font-extrabold tracking-tight bg-gradient-to-r from-primary via-blue-400 to-indigo-400 bg-clip-text text-transparent">TradeIntel AI</span>
            <span className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase leading-none">Automation Copilot</span>
          </div>
          <button className="ml-auto lg:hidden" onClick={() => setOpen(false)} data-testid="sidebar-close">
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex flex-col gap-0.5 overflow-y-auto p-3" style={{ height: "calc(100vh - 4rem)" }}>
          {NAV.map((item, idx) => item.divider ? (
            <div key={`div-${idx}`} className="mt-4 mb-1 px-3">
              <div className="flex items-center gap-2">
                <div className="h-px flex-1 bg-border/60" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">{item.label}</span>
                <div className="h-px flex-1 bg-border/60" />
              </div>
            </div>
          ) : (
            <NavLink key={item.to} to={item.to} onClick={() => setOpen(false)}
              data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, "-")}`}
              className={({ isActive }) => cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}>
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {open && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setOpen(false)} />}

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border/60 glass px-4">
          <button className="lg:hidden" onClick={() => setOpen(true)} data-testid="sidebar-open">
            <Menu className="h-5 w-5" />
          </button>
          <form onSubmit={doSearch} className="relative hidden max-w-sm flex-1 sm:block">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input data-testid="global-search" value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Search shipments, routes…"
              className="w-full rounded-md border border-border bg-background py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary" />
          </form>
          <div className="ml-auto flex items-center gap-1.5">
            <div className="hidden items-center gap-1 rounded-md border border-border px-2.5 py-1.5 text-xs text-muted-foreground md:flex" data-testid="org-selector">
              <Globe2 className="h-3.5 w-3.5" /> {org}
            </div>
            <Link to="/app/alerts" className="relative rounded-md p-2 hover:bg-accent" data-testid="topbar-alerts">
              <Bell className="h-5 w-5" />
              {unread > 0 && <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">{unread}</span>}
            </Link>
            <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")} className="rounded-md p-2 hover:bg-accent" data-testid="theme-toggle">
              <Sun className="hidden h-5 w-5 dark:block" />
              <Moon className="block h-5 w-5 dark:hidden" />
            </button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 rounded-md p-1 pr-2 hover:bg-accent" data-testid="user-menu">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">{initials}</span>
                  <span className="hidden text-sm font-medium md:block">{user?.name}</span>
                  <ChevronDown className="hidden h-4 w-4 text-muted-foreground md:block" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <p className="font-semibold">{user?.name}</p>
                  <p className="text-xs font-normal capitalize text-muted-foreground">{user?.role} · {user?.email}</p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate("/app/settings")} data-testid="menu-settings">
                  <Settings className="mr-2 h-4 w-4" /> Settings
                </DropdownMenuItem>
                <DropdownMenuItem onClick={async () => { await logout(); navigate("/login"); }} data-testid="menu-logout">
                  <LogOut className="mr-2 h-4 w-4" /> Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl space-y-6 ts-fade">{children}</div>
        </main>
      </div>
    </div>
  );
}
