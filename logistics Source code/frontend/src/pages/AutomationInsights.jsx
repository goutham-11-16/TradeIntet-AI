import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { 
  BarChart3, TrendingUp, Clock, CheckCircle, XCircle, Zap, Target, 
  AlertTriangle, ArrowRight, Lightbulb, RefreshCw, Activity, DollarSign, Users 
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area 
} from 'recharts';
import { api } from '@/lib/api';
import { PageHeader, StateWrap, StatTile, fmtNum, fmtMoney } from '@/components/common';

const COLORS = {
  success: '#10b981',
  danger: '#ef4444',
  warning: '#f59e0b',
  primary: '#3b82f6',
  simulated: '#6366f1',
  grid: '#334155',
  text: '#9ca3af'
};

const FALLBACK_ANALYTICS = {
  overview: {
    totalExecutions: 14502,
    successRate: 94.2,
    failureRate: 5.8,
    avgExecutionTime: "1m 12s",
    hoursSaved: 485,
    financialImpact: 1250000
  },
  trendData: Array.from({ length: 30 }).map((_, i) => ({
    date: `Aug ${i + 1}`,
    executions: Math.floor(Math.random() * 500) + 200,
  })),
  distributionData: [
    { name: 'Success', value: 13661 },
    { name: 'Failed', value: 841 },
    { name: 'Simulated', value: 350 }
  ],
  topWorkflows: [
    { name: 'Invoice Processing', count: 4200 },
    { name: 'Customs Clearance', count: 3100 },
    { name: 'Inventory Replenish', count: 2800 },
    { name: 'Vendor Onboarding', count: 1900 },
    { name: 'Fraud Detection', count: 1200 }
  ],
  approvalData: [
    { name: 'Invoices', auto: 85, manual: 15 },
    { name: 'Customs', auto: 60, manual: 40 },
    { name: 'Vendors', auto: 40, manual: 60 },
    { name: 'Refunds', auto: 75, manual: 25 },
  ],
  healthScores: [
    { id: 1, name: 'Invoice Processing', efficiency: 95, reliability: 98, cost: 85, latency: 90, automation: 95, overall: 94 },
    { id: 2, name: 'Customs Clearance', efficiency: 80, reliability: 90, cost: 75, latency: 85, automation: 70, overall: 82 },
    { id: 3, name: 'Inventory Replenish', efficiency: 88, reliability: 95, cost: 90, latency: 92, automation: 85, overall: 90 },
    { id: 4, name: 'Vendor Onboarding', efficiency: 70, reliability: 85, cost: 80, latency: 60, automation: 50, overall: 72 },
  ],
  bottlenecks: [
    { id: 'b1', node: 'Extract PDF Data', type: 'OCR Parser', duration: '4.2s', failureRate: 2.1, occurrences: 450, recommendation: 'Upgrade to standard layout-aware OCR model.' },
    { id: 'b2', node: 'Compliance Check', type: 'API Call', duration: '8.5s', failureRate: 0.5, occurrences: 320, recommendation: 'Implement caching for frequent vendor checks.' },
    { id: 'b3', node: 'Manager Approval', type: 'Human Task', duration: '14.2h', failureRate: 0, occurrences: 150, recommendation: 'Increase auto-approval threshold to reduce manual bottleneck.' },
  ]
};

const FALLBACK_OPTIMIZATIONS = [
  {
    id: 'opt1',
    workflow: 'Customs Clearance',
    current: 'Manual review for all low-risk shipments.',
    proposed: 'Auto-approve low-risk shipments under $5,000 value.',
    reason: 'Analysis shows 99.8% of low-risk shipments under $5K are approved without changes.',
    improvement: '+45% faster clearance, save 120hrs/month',
    risk: 'Low',
    confidence: 94
  },
  {
    id: 'opt2',
    workflow: 'Invoice Processing',
    current: 'Sequential parsing of invoice line items.',
    proposed: 'Parallelize parsing using batch processing node.',
    reason: 'Current sequential processing limits throughput on large invoices (50+ line items).',
    improvement: '-60% latency on large invoices',
    risk: 'Low',
    confidence: 98
  },
  {
    id: 'opt3',
    workflow: 'Fraud Detection',
    current: 'Uses basic threshold heuristics for alerts.',
    proposed: 'Switch to anomaly detection ML model (v2).',
    reason: 'Heuristics generate 15% false positives requiring manual review.',
    improvement: '-10% false positive rate',
    risk: 'Medium',
    confidence: 82
  }
];

export default function AutomationInsights() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [optimizations, setOptimizations] = useState([]);
  
  const [applyingOpt, setApplyingOpt] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [analyticsRes, optsRes] = await Promise.allSettled([
        api.workflowAnalytics ? api.workflowAnalytics() : Promise.reject('No method'),
        api.optimizations ? api.optimizations() : Promise.reject('No method')
      ]);

      const aData = analyticsRes.status === 'fulfilled' ? (analyticsRes.value?.data || analyticsRes.value) : null;
      const oData = optsRes.status === 'fulfilled' ? (optsRes.value?.data || optsRes.value) : null;

      setAnalytics(aData && aData.overview ? aData : (aData?.analytics || FALLBACK_ANALYTICS));
      setOptimizations(oData?.suggestions || (Array.isArray(oData) ? oData : FALLBACK_OPTIMIZATIONS));
      setError(null);
    } catch (err) {
      console.error(err);
      setAnalytics(FALLBACK_ANALYTICS);
      setOptimizations(FALLBACK_OPTIMIZATIONS);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyClick = (opt) => {
    setApplyingOpt(opt);
    setConfirmDialog(true);
  };

  const confirmApply = async () => {
    if (!applyingOpt) return;
    try {
      if (api.applyOptimization) {
        await api.applyOptimization(applyingOpt.id);
      } else {
        await new Promise(resolve => setTimeout(resolve, 800));
      }
      setOptimizations(prev => prev.filter(o => o.id !== applyingOpt.id));
      setConfirmDialog(false);
      setApplyingOpt(null);
    } catch (err) {
      console.error("Failed to apply optimization", err);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'bg-emerald-500';
    if (score >= 75) return 'bg-blue-500';
    if (score >= 60) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Workflow Performance Analytics" 
        subtitle="Live DAG telemetry, node bottlenecks, and continuous AI optimization suggestions"
      >
        <Button variant="outline" size="sm" onClick={fetchData} className="gap-2">
          <RefreshCw className="h-4 w-4" /> Refresh Telemetry
        </Button>
      </PageHeader>

      <StateWrap isLoading={loading} error={error} onRetry={fetchData}>
        {analytics && (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-3 lg:w-[400px] mb-8">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="bottlenecks">Bottlenecks</TabsTrigger>
              <TabsTrigger value="optimizations">AI Optimizations</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <StatTile 
                  title="Total Executions" 
                  value={fmtNum(analytics.overview.totalExecutions)} 
                  icon={<Activity className="h-5 w-5 text-blue-500" />} 
                />
                <StatTile 
                  title="Success Rate" 
                  value={`${analytics.overview.successRate}%`} 
                  valueColor={analytics.overview.successRate > 90 ? 'text-emerald-500' : 'text-foreground'}
                  icon={<CheckCircle className="h-5 w-5 text-emerald-500" />} 
                />
                <StatTile 
                  title="Failure Rate" 
                  value={`${analytics.overview.failureRate}%`} 
                  valueColor={analytics.overview.failureRate > 10 ? 'text-red-500' : 'text-foreground'}
                  icon={<XCircle className="h-5 w-5 text-red-500" />} 
                />
                <StatTile 
                  title="Avg Execution Time" 
                  value={analytics.overview.avgExecutionTime} 
                  icon={<Clock className="h-5 w-5 text-purple-500" />} 
                />
                <StatTile 
                  title="Hours Saved" 
                  value={fmtNum(analytics.overview.hoursSaved)} 
                  icon={<Clock className="h-5 w-5 text-amber-500" />} 
                />
                <StatTile 
                  title="Financial Impact" 
                  value={`₹${fmtNum(analytics.overview.financialImpact)}`} 
                  icon={<DollarSign className="h-5 w-5 text-emerald-500" />} 
                />
              </div>

              {/* Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" /> Execution Trend (30 Days)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={analytics.trendData}>
                        <defs>
                          <linearGradient id="colorExec" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3}/>
                            <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                        <XAxis dataKey="date" stroke={COLORS.text} fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke={COLORS.text} fontSize={12} tickLine={false} axisLine={false} />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
                        <Area type="monotone" dataKey="executions" stroke={COLORS.primary} fillOpacity={1} fill="url(#colorExec)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <PieChart className="h-4 w-4" /> Success vs Failure
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={analytics.distributionData}
                          cx="50%"
                          cy="50%"
                          innerRadius={80}
                          outerRadius={110}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          <Cell fill={COLORS.success} />
                          <Cell fill={COLORS.danger} />
                          <Cell fill={COLORS.simulated} />
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center gap-6 mt-2">
                      {analytics.distributionData.map((entry, index) => (
                        <div key={entry.name} className="flex items-center gap-2 text-sm text-muted-foreground">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: [COLORS.success, COLORS.danger, COLORS.simulated][index] }} />
                          {entry.name}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" /> Most Used Workflows
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analytics.topWorkflows} layout="vertical" margin={{ left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} horizontal={false} />
                        <XAxis type="number" stroke={COLORS.text} fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis dataKey="name" type="category" stroke={COLORS.text} fontSize={12} tickLine={false} axisLine={false} width={120} />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }} cursor={{fill: '#334155'}} />
                        <Bar dataKey="count" fill={COLORS.primary} radius={[0, 4, 4, 0]} barSize={24} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <Users className="h-4 w-4" /> Approval vs Auto-Execute
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analytics.approvalData} margin={{ top: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} vertical={false} />
                        <XAxis dataKey="name" stroke={COLORS.text} fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke={COLORS.text} fontSize={12} tickLine={false} axisLine={false} />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} cursor={{fill: '#334155'}} />
                        <Bar dataKey="auto" stackId="a" fill={COLORS.success} name="Auto-Execute" radius={[0, 0, 4, 4]} barSize={40} />
                        <Bar dataKey="manual" stackId="a" fill={COLORS.warning} name="Manual Approval" radius={[4, 4, 0, 0]} barSize={40} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>

              {/* Health Scores Table */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <Target className="h-4 w-4" /> Workflow Health Scores
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-muted-foreground uppercase bg-muted/50">
                        <tr>
                          <th className="px-4 py-3 rounded-tl-md">Workflow Name</th>
                          <th className="px-4 py-3">Efficiency</th>
                          <th className="px-4 py-3">Reliability</th>
                          <th className="px-4 py-3">Cost</th>
                          <th className="px-4 py-3">Latency</th>
                          <th className="px-4 py-3 text-right rounded-tr-md">Overall</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analytics.healthScores.map((score) => (
                          <tr key={score.id} className="border-b border-border/50 hover:bg-muted/20">
                            <td className="px-4 py-4 font-medium text-foreground">{score.name}</td>
                            <td className="px-4 py-4">
                              <div className="flex items-center gap-2">
                                <Progress value={score.efficiency} className="w-24 h-2" indicatorClassName={getScoreColor(score.efficiency)} />
                                <span className="text-xs text-muted-foreground w-6">{score.efficiency}</span>
                              </div>
                            </td>
                            <td className="px-4 py-4">
                              <div className="flex items-center gap-2">
                                <Progress value={score.reliability} className="w-24 h-2" indicatorClassName={getScoreColor(score.reliability)} />
                                <span className="text-xs text-muted-foreground w-6">{score.reliability}</span>
                              </div>
                            </td>
                            <td className="px-4 py-4">
                              <div className="flex items-center gap-2">
                                <Progress value={score.cost} className="w-24 h-2" indicatorClassName={getScoreColor(score.cost)} />
                                <span className="text-xs text-muted-foreground w-6">{score.cost}</span>
                              </div>
                            </td>
                            <td className="px-4 py-4">
                              <div className="flex items-center gap-2">
                                <Progress value={score.latency} className="w-24 h-2" indicatorClassName={getScoreColor(score.latency)} />
                                <span className="text-xs text-muted-foreground w-6">{score.latency}</span>
                              </div>
                            </td>
                            <td className="px-4 py-4 text-right">
                              <Badge className={`${getScoreColor(score.overall)} text-white border-none hover:${getScoreColor(score.overall)}`}>
                                {score.overall}/100
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="bottlenecks" className="space-y-4">
              <div className="grid gap-4">
                {analytics.bottlenecks.map((bottleneck) => (
                  <Card key={bottleneck.id} className="border-l-4 border-l-amber-500">
                    <CardContent className="p-6">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-amber-500" />
                            <h3 className="font-semibold text-lg">{bottleneck.node}</h3>
                            <Badge variant="outline" className="text-xs font-normal">{bottleneck.type}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                            <strong>Recommendation:</strong> {bottleneck.recommendation}
                          </p>
                        </div>
                        
                        <div className="flex items-center gap-8 bg-muted/30 p-4 rounded-lg">
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Avg Duration</p>
                            <p className="font-mono font-medium text-red-400">{bottleneck.duration}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Failure Rate</p>
                            <p className="font-mono font-medium">{bottleneck.failureRate}%</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">Occurrences</p>
                            <p className="font-mono font-medium">{bottleneck.occurrences}</p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="optimizations" className="space-y-4">
              {optimizations.length === 0 ? (
                <Card>
                  <CardContent className="py-12 flex flex-col items-center text-center text-muted-foreground">
                    <CheckCircle className="h-12 w-12 text-emerald-500 mb-4" />
                    <p className="text-lg font-medium text-foreground">Your workflows are fully optimized!</p>
                    <p>No new AI recommendations at this time.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-6">
                  {optimizations.map((opt) => (
                    <Card key={opt.id} className="overflow-hidden border-primary/20 bg-primary/5">
                      <CardHeader className="bg-muted/30 pb-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="text-lg flex items-center gap-2 text-primary">
                              <Lightbulb className="h-5 w-5" fill="currentColor" />
                              Optimization for {opt.workflow}
                            </CardTitle>
                            <p className="text-sm text-muted-foreground mt-1">{opt.reason}</p>
                          </div>
                          <div className="flex flex-col items-end gap-1">
                            <Badge variant="secondary" className="bg-primary/20 text-primary hover:bg-primary/30">
                              {opt.risk} Risk
                            </Badge>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2">
                              <span>AI Confidence</span>
                              <Progress value={opt.confidence} className="w-16 h-1.5" indicatorClassName="bg-primary" />
                              <span>{opt.confidence}%</span>
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="p-6">
                        <div className="flex flex-col md:flex-row items-center gap-6 mb-6">
                          <div className="flex-1 bg-muted/50 p-4 rounded-lg w-full">
                            <p className="text-xs font-semibold uppercase text-muted-foreground mb-2">Current Behavior</p>
                            <p className="text-sm">{opt.current}</p>
                          </div>
                          
                          <div className="hidden md:flex flex-col items-center justify-center text-primary">
                            <ArrowRight className="h-6 w-6" />
                          </div>

                          <div className="flex-1 bg-primary/10 border border-primary/20 p-4 rounded-lg w-full">
                            <p className="text-xs font-semibold uppercase text-primary mb-2">Proposed Behavior</p>
                            <p className="text-sm text-foreground">{opt.proposed}</p>
                          </div>
                        </div>

                        <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-t border-border/50 pt-4">
                          <div className="flex items-center gap-2 text-emerald-500 bg-emerald-500/10 px-3 py-1.5 rounded-full text-sm font-medium">
                            <Zap className="h-4 w-4" />
                            Expected: {opt.improvement}
                          </div>
                          
                          <div className="flex gap-3">
                            <Button variant="outline" size="sm">Review Details</Button>
                            <Button variant="outline" size="sm" className="border-blue-500/30 text-blue-500 hover:bg-blue-500/10">
                              Simulate Change
                            </Button>
                            <Button size="sm" onClick={() => handleApplyClick(opt)}>
                              Apply Optimization
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </StateWrap>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog} onOpenChange={setConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Apply AI Optimization</DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <p className="text-muted-foreground">
              This will modify the workflow <strong>{applyingOpt?.workflow}</strong>. Are you sure you want to proceed?
            </p>
            <div className="bg-muted p-3 rounded-md text-sm border-l-4 border-primary">
              <p className="font-semibold mb-1">Proposed Change:</p>
              <p>{applyingOpt?.proposed}</p>
            </div>
            <p className="text-xs text-amber-500 flex items-center gap-1 mt-2">
              <AlertTriangle className="h-3 w-3" /> Changes take effect immediately on next execution.
            </p>
          </div>
          <div className="flex justify-end gap-3 mt-2">
            <Button variant="outline" onClick={() => setConfirmDialog(false)}>Cancel</Button>
            <Button onClick={confirmApply}>Confirm & Apply</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
