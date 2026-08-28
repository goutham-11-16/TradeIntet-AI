import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  AlertTriangle, ShieldAlert, GitMerge, RotateCcw, Eye, 
  CheckCircle, XCircle, ArrowRight, RefreshCw, Zap,
  ChevronDown, ChevronUp, ShieldCheck
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { PageHeader, StateWrap } from '@/components/common';
import { toast } from 'sonner';

export default function ConflictCenter() {
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [resolvedIds, setResolvedIds] = useState(new Set());
  
  const [stats, setStats] = useState({ total: 0, critical: 0, high: 0, resolved: 0 });
  const navigate = useNavigate();

  const calculateStats = (data, resolvedSet = resolvedIds) => {
    const activeConflicts = data.filter(c => !resolvedSet.has(c.id));
    const total = data.length;
    const critical = activeConflicts.filter(c => c.severity === 'CRITICAL').length;
    const high = activeConflicts.filter(c => c.severity === 'HIGH').length;
    setStats({ total, critical, high, resolved: resolvedSet.size });
  };

  const fetchConflicts = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.allConflicts();
      const data = res?.data || res;
      const list = data?.conflicts || (Array.isArray(data) ? data : []);
      setConflicts(list);
      calculateStats(list);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch conflicts:', err);
      setError(err.message || 'Failed to fetch conflicts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConflicts();
  }, [fetchConflicts]);

  const handleScan = async () => {
    try {
      setScanning(true);
      const res = await api.detectConflicts({ check_all: true });
      const data = res?.data || res;
      const list = data?.conflicts || (Array.isArray(data) ? data : []);
      setConflicts(list);
      calculateStats(list);
      toast.success(`Conflict engine scan complete. ${list.length} conflicts evaluated.`);
    } catch (err) {
      console.error(err);
      toast.error('Failed to scan workflows');
    } finally {
      setScanning(false);
    }
  };

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleResolve = (id, action) => {
    const nextResolved = new Set(resolvedIds);
    nextResolved.add(id);
    setResolvedIds(nextResolved);
    calculateStats(conflicts, nextResolved);
    toast.success(`Conflict resolved (${action})`);
  };

  const getSeverityColor = (severity) => {
    switch((severity || '').toUpperCase()) {
      case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'HIGH': return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'MEDIUM': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';
      case 'LOW': return 'bg-sky-500/20 text-sky-400 border-sky-500/40';
      default: return 'bg-slate-500/20 text-slate-400 border-slate-500/40';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <PageHeader 
          title="Conflict & Governance Center" 
          subtitle="Multi-Workflow collision, loop, and approval bypass detection" 
        />
        <Button onClick={handleScan} disabled={scanning} className="gap-2 shadow-sm">
          <RefreshCw className={`h-4 w-4 ${scanning ? 'animate-spin' : ''}`} />
          {scanning ? 'Scanning Matrix...' : 'Scan All Workflows'}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border/60 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Total Conflicts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{stats.total}</div>
            <p className="text-xs text-muted-foreground mt-1">Multi-workflow checks</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/60 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-red-400 font-semibold uppercase tracking-wider">Critical (Bypasses)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-400">{stats.critical}</div>
            <p className="text-xs text-muted-foreground mt-1">Policy violations &gt; ₹10L</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/60 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-amber-400 font-semibold uppercase tracking-wider">High (Collisions)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-400">{stats.high}</div>
            <p className="text-xs text-muted-foreground mt-1">Simultaneous triggers</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/60 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-emerald-400 font-semibold uppercase tracking-wider">Mitigated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-400">{stats.resolved}</div>
            <p className="text-xs text-muted-foreground mt-1">Resolved via policy rules</p>
          </CardContent>
        </Card>
      </div>

      <StateWrap isLoading={loading} error={error} onRetry={fetchConflicts}>
        <div className="space-y-4">
          {conflicts.length === 0 ? (
            <div className="text-center p-12 text-muted-foreground border border-border/60 rounded-xl bg-card/50">
              <CheckCircle className="h-12 w-12 mx-auto mb-3 text-emerald-500/60" />
              <p className="font-semibold text-foreground">No conflicts detected in your workflow graph.</p>
              <p className="text-xs text-muted-foreground mt-1">All triggers, conditions, and governance approval gates are consistent.</p>
            </div>
          ) : (
            conflicts.map((conflict) => {
              const isResolved = resolvedIds.has(conflict.id);

              return (
                <Card key={conflict.id} className={`bg-card border-border/60 overflow-hidden shadow-md transition-all ${isResolved ? 'opacity-50 border-emerald-500/30' : 'hover:border-border'}`}>
                  <div className="p-4 flex items-start justify-between cursor-pointer" onClick={() => toggleExpand(conflict.id)}>
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className={getSeverityColor(conflict.severity)}>
                          {conflict.severity}
                        </Badge>
                        <Badge variant="secondary" className="bg-secondary/70 text-xs font-mono">
                          {conflict.type}
                        </Badge>
                        {isResolved && (
                          <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                            <CheckCircle className="w-3 h-3 mr-1 inline" /> Resolved
                          </Badge>
                        )}
                      </div>
                      <div className="font-semibold text-base flex items-center gap-2 text-foreground">
                        <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
                        {conflict.workflows?.join(' ⚡ ') || conflict.name || 'Workflow Collision'}
                      </div>
                      <p className="text-muted-foreground text-xs leading-relaxed">{conflict.explanation}</p>
                    </div>
                    <div className="pt-2 pl-4">
                      {expandedId === conflict.id ? <ChevronUp className="h-5 w-5 text-muted-foreground" /> : <ChevronDown className="h-5 w-5 text-muted-foreground" />}
                    </div>
                  </div>
                  
                  {expandedId === conflict.id && (
                    <div className="px-5 pb-5 border-t border-border/60 pt-4 bg-muted/20">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                          <div>
                            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Issue Overview</h4>
                            <p className="text-sm text-slate-300 leading-relaxed">{conflict.explanation}</p>
                          </div>
                          <div>
                            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Operational Impact</h4>
                            <p className="text-sm text-slate-300 leading-relaxed">{conflict.potential_impact || 'Conflicting automated operations could cause duplicate rerouting or unapproved spend.'}</p>
                          </div>
                          {conflict.affected_nodes?.length > 0 && (
                            <div>
                              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">Affected Nodes</h4>
                              <div className="flex flex-wrap gap-2">
                                {conflict.affected_nodes.map((node, i) => (
                                  <Badge key={i} variant="outline" className="text-xs bg-background/80 font-mono">
                                    {node}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <div className="space-y-4 bg-background/60 p-4 rounded-xl border border-border/60 flex flex-col justify-between">
                          <div>
                            <h4 className="text-xs font-semibold text-primary flex items-center gap-1.5 mb-2 uppercase tracking-wider">
                              <Zap className="h-4 w-4 text-primary" /> Recommended Governance Fix
                            </h4>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                              {conflict.recommended_fix || 'Insert an Approval Gate Node before route execution for shipments with declared value > ₹10,00,000.'}
                            </p>
                          </div>
                          
                          <div className="pt-4 flex flex-wrap gap-2 border-t border-border/40">
                            <Button 
                              size="sm" 
                              variant="default" 
                              className="gap-1.5 text-xs"
                              onClick={() => {
                                toast.info('Opening Workflow Studio');
                                navigate('/app/workflows');
                              }}
                            >
                              <Eye className="h-3.5 w-3.5" /> View in Studio
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="gap-1.5 text-xs text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10"
                              onClick={() => handleResolve(conflict.id, 'Approval Rule Injected')}
                            >
                              <ShieldCheck className="h-3.5 w-3.5" /> Apply Rule
                            </Button>
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              className="gap-1.5 text-xs text-slate-400 hover:text-white"
                              onClick={() => handleResolve(conflict.id, 'Ignored')}
                            >
                              Dismiss
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </Card>
              );
            })
          )}
        </div>
      </StateWrap>
    </div>
  );
}
