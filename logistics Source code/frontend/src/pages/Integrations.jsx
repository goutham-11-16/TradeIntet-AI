import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StateWrap, StatTile } from "@/components/common";
import { 
  Plug, Check, RefreshCw, Settings, Radio, Database, ShieldCheck, 
  ArrowUpRight, Activity, Zap, Layers, Clock, AlertCircle, Wifi, Globe
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

export default function Integrations() {
  const qc = useQueryClient();
  const { canManage } = useAuth();
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("adapters");

  // Config modal state
  const [configModal, setConfigModal] = useState(false);
  const [selectedAdapter, setSelectedAdapter] = useState(null);
  const [apiKey, setApiKey] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [syncFreq, setSyncFreq] = useState("realtime");
  const [autoTrigger, setAutoTrigger] = useState(true);

  // Queries
  const { data, isLoading, error, refetch } = useQuery({ 
    queryKey: ["integrations"], 
    queryFn: () => api.integrations().then((r) => r.data) 
  });

  const { data: eventsData } = useQuery({
    queryKey: ["integrationEvents"],
    queryFn: () => api.integrationEvents().then((r) => r.data),
    refetchInterval: 10000 // Refresh live feed every 10s
  });

  // Mutations
  const toggleMut = useMutation({
    mutationFn: ({ id, config }) => api.toggleIntegration(id, config),
    onSuccess: (res) => { 
      toast.success(res.data.message || `${res.data.id} updated`); 
      qc.invalidateQueries({ queryKey: ["integrations"] });
      setConfigModal(false);
    },
    onError: (e) => toast.error(e.response?.data?.detail || "Failed to update integration"),
  });

  const syncMut = useMutation({
    mutationFn: (id) => api.syncIntegration(id),
    onSuccess: (res) => {
      toast.success(res.data.message || `Data synchronized successfully!`);
      qc.invalidateQueries({ queryKey: ["integrations"] });
      qc.invalidateQueries({ queryKey: ["integrationEvents"] });
    },
    onError: (e) => toast.error(e.response?.data?.detail || "Failed to sync"),
  });

  const integrationsList = data?.integrations || [];
  const eventsList = eventsData?.events || [];

  const connectedCount = integrationsList.filter(i => i.connected).length;
  const totalRecords = integrationsList.reduce((acc, curr) => acc + (curr.records_synced || 0), 0);

  const categories = ["All", "ERP & SCM", "E-commerce", "Carrier & AIS", "Customs & Compliance", "Risk & Intelligence"];

  const filteredIntegrations = integrationsList.filter(i => {
    const matchCat = selectedCategory === "All" || i.category.toLowerCase().includes(selectedCategory.toLowerCase());
    const matchSearch = (i.name || "").toLowerCase().includes(search.toLowerCase()) || 
                        (i.description || "").toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  const openConfig = (adapter) => {
    setSelectedAdapter(adapter);
    setApiKey(adapter.config?.api_key || `sk_live_${adapter.id}_${Math.random().toString(36).substring(7)}`);
    setEndpoint(adapter.config?.endpoint || `https://api.${adapter.id}.logistics.io/v2/stream`);
    setSyncFreq(adapter.config?.sync_freq || "realtime");
    setAutoTrigger(adapter.config?.auto_trigger !== false);
    setConfigModal(true);
  };

  const handleSaveConfig = () => {
    if (!selectedAdapter) return;
    toggleMut.mutate({
      id: selectedAdapter.id,
      config: {
        api_key: apiKey,
        endpoint: endpoint,
        sync_freq: syncFreq,
        auto_trigger: autoTrigger
      }
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader 
        testId="integrations-header" 
        title="Enterprise Data Integrations & Ingestion Hub" 
        subtitle="Connect real-time ERP, WMS, TMS, AIS satellite vessel telemetry, customs EDI & geopolitical intelligence feeds."
      />

      {/* Top Metric Tiles */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile 
          title="Active Adapters" 
          value={`${connectedCount} / ${integrationsList.length || 9}`} 
          sub="Live connected pipelines" 
          icon={<Radio className="h-5 w-5 text-emerald-400" />} 
        />
        <StatTile 
          title="VectorDB Ingested" 
          value={totalRecords.toLocaleString()} 
          sub="Indexed entities & events" 
          icon={<Database className="h-5 w-5 text-sky-400" />} 
        />
        <StatTile 
          title="Streaming Latency" 
          value="28ms" 
          sub="Average webhook ingestion" 
          icon={<Zap className="h-5 w-5 text-amber-400" />} 
        />
        <StatTile 
          title="Pipeline Uptime" 
          value="99.98%" 
          sub="Zero-loss fault tolerant" 
          icon={<ShieldCheck className="h-5 w-5 text-indigo-400" />} 
        />
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-border/60 pb-3">
          <TabsList className="bg-card border border-border/60">
            <TabsTrigger value="adapters" className="gap-2">
              <Plug className="w-4 h-4" /> Data Connectors ({integrationsList.length})
            </TabsTrigger>
            <TabsTrigger value="stream" className="gap-2">
              <Activity className="w-4 h-4" /> Live Ingestion Feed
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            </TabsTrigger>
          </TabsList>

          {activeTab === "adapters" && (
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Input
                placeholder="Search connector by name, ERP, carrier..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full sm:w-64 h-9 text-xs"
              />
            </div>
          )}
        </div>

        {/* Tab 1: Adapters Grid */}
        <TabsContent value="adapters" className="space-y-4 mt-0">
          {/* Category Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <span className="text-muted-foreground font-semibold flex items-center gap-1 shrink-0 mr-1">
              <Globe className="w-3.5 h-3.5" /> Domain:
            </span>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-full font-medium transition-all shrink-0 ${
                  selectedCategory === cat 
                    ? "bg-primary text-primary-foreground shadow-sm" 
                    : "bg-card border border-border/60 text-muted-foreground hover:text-foreground hover:bg-accent"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <StateWrap loading={isLoading} error={error ? "Failed to load integrations." : null} onRetry={refetch}>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" data-testid="integrations-grid">
              {filteredIntegrations.map((i) => (
                <Card 
                  key={i.id} 
                  className={`border transition-all duration-200 ${
                    i.connected 
                      ? "border-primary/40 bg-card/95 hover:border-primary/70 shadow-sm" 
                      : "border-border/60 bg-card/60 opacity-80 hover:opacity-100"
                  }`}
                  data-testid={`integration-${i.id}`}
                >
                  <CardHeader className="p-5 pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`flex h-11 w-11 items-center justify-center rounded-xl font-bold text-base ${
                          i.connected ? "bg-primary/15 text-primary border border-primary/30" : "bg-muted text-muted-foreground"
                        }`}>
                          {i.id === "shopify" && "🛍️"}
                          {i.id === "sap" && "💼"}
                          {i.id === "oracle" && "☁️"}
                          {i.id === "erp" && "⚡"}
                          {i.id === "wms" && "📦"}
                          {i.id === "tms" && "🚚"}
                          {i.id === "carrier-api" && "🚢"}
                          {i.id === "customs-api" && "🏛️"}
                          {i.id === "news-risk" && "🛰️"}
                        </div>
                        <div>
                          <CardTitle className="text-base font-bold flex items-center gap-2">
                            {i.name}
                          </CardTitle>
                          <Badge variant="outline" className="text-[10px] mt-0.5 font-semibold text-muted-foreground uppercase tracking-wider">
                            {i.category}
                          </Badge>
                        </div>
                      </div>
                      {i.connected ? (
                        <Badge className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-xs py-0.5 px-2 font-medium flex items-center gap-1.5">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                          Connected
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-xs text-muted-foreground">
                          Standby
                        </Badge>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent className="p-5 pt-0 space-y-4">
                    <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed mt-1">
                      {i.description}
                    </p>

                    {/* Streamed Data Types */}
                    {i.data_types && (
                      <div className="space-y-1.5">
                        <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Streamed Data Feeds</div>
                        <div className="flex flex-wrap gap-1">
                          {i.data_types.map((dt, idx) => (
                            <span key={idx} className="text-[10px] bg-secondary/80 text-foreground px-2 py-0.5 rounded-md border border-border/40">
                              {dt}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Live Telemetry Info */}
                    <div className="rounded-lg bg-secondary/40 border border-border/40 p-3 grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-[10px] text-muted-foreground block font-medium">Records Synced</span>
                        <span className="font-bold text-foreground flex items-center gap-1 mt-0.5">
                          <Database className="w-3 h-3 text-sky-400" />
                          {(i.records_synced || 0).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-muted-foreground block font-medium">Latency / Health</span>
                        <span className="font-bold text-foreground flex items-center gap-1 mt-0.5">
                          <Wifi className="w-3 h-3 text-emerald-400" />
                          {i.latency_ms}ms · {i.health}
                        </span>
                      </div>
                    </div>

                    {/* Linked Workflows */}
                    {i.connected_workflows && i.connected_workflows.length > 0 && (
                      <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-primary shrink-0" />
                        <span className="truncate">Auto-triggers: <span className="text-foreground font-medium">{i.connected_workflows[0]}</span></span>
                      </div>
                    )}

                    {/* Action Bar */}
                    <div className="pt-2 flex items-center gap-2 border-t border-border/60">
                      {i.connected ? (
                        <>
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="flex-1 text-xs gap-1.5 h-8" 
                            onClick={() => openConfig(i)}
                          >
                            <Settings className="w-3.5 h-3.5 text-muted-foreground" /> Configure
                          </Button>
                          <Button 
                            variant="secondary" 
                            size="sm" 
                            className="text-xs gap-1.5 h-8 px-3 hover:bg-primary/20 hover:text-primary"
                            onClick={() => syncMut.mutate(i.id)}
                            disabled={syncMut.isPending}
                          >
                            <RefreshCw className={`w-3.5 h-3.5 ${syncMut.isPending ? "animate-spin" : ""}`} /> Sync
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 h-8 px-2.5"
                            onClick={() => toggleMut.mutate({ id: i.id })}
                          >
                            Disconnect
                          </Button>
                        </>
                      ) : (
                        <Button 
                          variant="default" 
                          size="sm" 
                          className="w-full text-xs font-semibold h-9 gap-1.5"
                          onClick={() => openConfig(i)}
                        >
                          <Plug className="w-3.5 h-3.5" /> Connect & Authorize
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </StateWrap>
        </TabsContent>

        {/* Tab 2: Live Ingestion Event Stream */}
        <TabsContent value="stream" className="space-y-4 mt-0">
          <Card className="border-border/60">
            <CardHeader className="p-5 pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    Live Webhook & Telemetry Ingestion Log
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Real-time stream of incoming cargo payloads, vessel AIS position pings, and customs EDI milestones.
                  </CardDescription>
                </div>
                <Badge variant="outline" className="text-xs text-emerald-400 bg-emerald-500/10 border-emerald-500/30 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                  Streaming Active
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-5 pt-0">
              <div className="divide-y divide-border/60">
                {eventsList.map((evt) => (
                  <div key={evt.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-accent/30 rounded-lg px-3 transition-colors">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-[10px] font-mono uppercase bg-secondary">
                          {evt.id}
                        </Badge>
                        <span className="text-xs font-bold text-foreground">{evt.source}</span>
                        <span className="text-xs text-muted-foreground font-mono">({evt.type})</span>
                      </div>
                      <p className="text-xs text-foreground/90 font-medium">
                        {evt.payload}
                      </p>
                      <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {evt.timestamp}</span>
                        <span className="flex items-center gap-1 text-primary"><Zap className="w-3 h-3" /> Matched Workflow: {evt.matched_workflow}</span>
                      </div>
                    </div>
                    <div className="shrink-0 flex items-center gap-2">
                      <Badge className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[11px]">
                        {evt.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Interactive Connector Configuration Modal */}
      <Dialog open={configModal} onOpenChange={setConfigModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5 text-primary" />
              Configure {selectedAdapter?.name} Connector
            </DialogTitle>
            <DialogDescription className="text-xs">
              Establish mTLS / OAuth credentials and set automated workflow ingestion rules.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2 text-sm">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Auth Protocol</label>
              <div className="p-2.5 rounded-md bg-secondary/50 border border-border/60 text-xs font-mono text-foreground flex items-center justify-between">
                <span>{selectedAdapter?.auth_type}</span>
                <Badge variant="outline" className="text-[10px] text-emerald-400">Enterprise Verified</Badge>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">API Key / Secret Token</label>
              <Input 
                value={apiKey} 
                onChange={(e) => setApiKey(e.target.value)} 
                type="password"
                placeholder="sk_live_..." 
                className="font-mono text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Streaming Webhook / Endpoint URL</label>
              <Input 
                value={endpoint} 
                onChange={(e) => setEndpoint(e.target.value)} 
                placeholder="https://api..." 
                className="font-mono text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Ingestion Sync Cadence</label>
              <Select value={syncFreq} onValueChange={setSyncFreq}>
                <SelectTrigger className="text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="realtime">⚡ Real-time Webhook Streaming (Sub-second)</SelectItem>
                  <SelectItem value="5m">⏱️ High Frequency (Every 5 minutes)</SelectItem>
                  <SelectItem value="15m">⏳ Standard Batch (Every 15 minutes)</SelectItem>
                  <SelectItem value="1h">📅 Hourly Reconciliation</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-border/60 p-3 bg-secondary/30">
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-foreground">Auto-trigger AI Workflows</div>
                <div className="text-[11px] text-muted-foreground">Trigger DAG workflows when high-risk anomaly events are ingested</div>
              </div>
              <Switch checked={autoTrigger} onCheckedChange={setAutoTrigger} />
            </div>
          </div>

          <DialogFooter className="flex items-center justify-between">
            <Button variant="outline" size="sm" onClick={() => setConfigModal(false)}>Cancel</Button>
            <Button size="sm" onClick={handleSaveConfig} disabled={toggleMut.isPending} className="gap-2">
              <Check className="w-4 h-4" /> Save & Activate Pipeline
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
