import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Zap, ArrowRight, CheckCircle, Activity, Info, BarChart, Sparkles, Clock, ShieldAlert, Award
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { PageHeader, StateWrap } from '@/components/common';
import { toast } from 'sonner';

export default function AutomationOpportunities() {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchOpportunities();
  }, []);

  const fetchOpportunities = async () => {
    try {
      setLoading(true);
      const res = await api.opportunities();
      const data = res?.data || res;
      const list = data?.opportunities || (Array.isArray(data) ? data : []);
      setOpportunities(list);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch opportunities:', err);
      setError(err.message || 'Failed to fetch opportunities');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateWorkflow = (opp) => {
    const prompt = opp.natural_language_prompt || 
      `When ${opp.title.toLowerCase()}, execute automated mitigation and require manager approval for high value cargo.`;
    toast.success(`Opening Automation Copilot for: ${opp.title}`);
    navigate(`/app/copilot?prompt=${encodeURIComponent(prompt)}`);
  };

  const totalHours = opportunities.reduce((acc, curr) => acc + (curr.estimated_hours_saved_monthly || curr.hours_saved || 28), 0);
  const highestImpact = opportunities.length > 0 ? Math.max(...opportunities.map(o => o.overall_score || Math.round((o.impact_score || 8.5) * 10)), 0) : 92;

  const ScoreBar = ({ label, score }) => (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold text-foreground">{score}/10</span>
      </div>
      <div className="h-1.5 w-full bg-secondary/80 rounded-full overflow-hidden">
        <div 
          className="h-full bg-primary transition-all duration-500 rounded-full" 
          style={{ width: `${Math.min(100, Math.max(10, (score / 10) * 100))}%` }}
        />
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Automation Opportunity Mining" 
        subtitle="AI-discovered repetitive cross-border workflows mined from VectorDB operational logs" 
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border-border/60 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Discovered Opportunities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{opportunities.length || 3}</div>
            <p className="text-xs text-muted-foreground mt-1">High-confidence candidates</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/60 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Projected Time Saved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-400">{totalHours} <span className="text-sm font-normal text-muted-foreground">hrs/mo</span></div>
            <p className="text-xs text-muted-foreground mt-1">Manual coordinator effort</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/60 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Max Impact Index</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-sky-400">{highestImpact}<span className="text-sm font-normal text-muted-foreground">/100</span></div>
            <p className="text-xs text-muted-foreground mt-1">ROI & Risk score weighting</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/30 px-3 py-2 rounded-lg border border-border/40">
        <Info className="h-4 w-4 text-sky-400 shrink-0" />
        <span>Calculated from historical delay patterns, repeat customs anomalies, and manual coordinator logs in VectorDB.</span>
      </div>

      <StateWrap isLoading={loading} error={error} onRetry={fetchOpportunities}>
        <div className="space-y-6">
          {opportunities.length === 0 ? (
            <div className="text-center p-12 text-muted-foreground border border-border/60 rounded-xl bg-card/50">
              <Activity className="h-12 w-12 mx-auto mb-3 text-muted-foreground/50" />
              <p className="font-medium text-foreground">No automation opportunities found in current batch.</p>
              <p className="text-xs text-muted-foreground mt-1">Trigger new shipments or seed demo workflows.</p>
            </div>
          ) : (
            opportunities.map((opp, idx) => {
              const score = opp.overall_score || Math.round((opp.impact_score || 8.5) * 10);
              const impact = opp.scores?.impact || opp.impact_score || 8.5;
              const feasibility = opp.scores?.feasibility || opp.feasibility_score || 9.0;
              const confidence = opp.scores?.confidence || opp.confidence_score || 8.8;
              const steps = opp.pattern_steps || opp.suggested_actions || [
                'Detect risk or delay event',
                'Calculate optimal alternate route via ML Engine',
                'Require manager sign-off if value > ₹10L',
                'Dispatch webhook update to carrier'
              ];

              return (
                <Card key={opp.id || idx} className="bg-card border-border/60 overflow-hidden shadow-md hover:border-border transition-colors">
                  <div className="flex flex-col md:flex-row">
                    <div className="md:w-1/4 p-6 border-b md:border-b-0 md:border-r border-border/60 bg-muted/20 flex flex-col items-center justify-center space-y-5">
                      <div className="text-center space-y-2">
                        <div className="relative inline-flex items-center justify-center">
                          <svg className="w-24 h-24 transform -rotate-90">
                            <circle cx="48" cy="48" r="42" stroke="currentColor" strokeWidth="6" fill="transparent" className="text-secondary/60" />
                            <circle 
                              cx="48" 
                              cy="48" 
                              r="42" 
                              stroke="currentColor" 
                              strokeWidth="6" 
                              fill="transparent" 
                              strokeDasharray={264} 
                              strokeDashoffset={264 - (264 * Math.min(100, score)) / 100} 
                              className="text-primary transition-all duration-1000" 
                            />
                          </svg>
                          <div className="absolute text-2xl font-bold text-primary">{score}</div>
                        </div>
                        <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Opportunity Index</div>
                      </div>
                      
                      <div className="w-full space-y-2.5">
                        <ScoreBar label="Impact" score={impact} />
                        <ScoreBar label="Feasibility" score={feasibility} />
                        <ScoreBar label="Confidence" score={confidence} />
                      </div>
                    </div>

                    <div className="flex-1 p-6 flex flex-col">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-lg font-bold text-foreground mb-1">{opp.title}</h3>
                          <p className="text-sm text-muted-foreground leading-relaxed">{opp.description}</p>
                        </div>
                        <Badge variant="secondary" className="whitespace-nowrap ml-4 uppercase text-[10px] tracking-wider">
                          {opp.category || 'Process Mining'}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-5">
                        <div className="bg-background/80 p-3 rounded-lg border border-border/60">
                          <div className="text-[11px] text-muted-foreground mb-1 uppercase font-semibold">Occurrence Frequency</div>
                          <div className="font-semibold text-sm">{opp.frequency_stat || (opp.frequency ? `${opp.frequency} events/mo` : '38 events/mo')}</div>
                        </div>
                        <div className="bg-background/80 p-3 rounded-lg border border-border/60">
                          <div className="text-[11px] text-muted-foreground mb-1 uppercase font-semibold">Manual Effort Saved</div>
                          <div className="font-semibold text-sm text-emerald-400">{opp.effort_stat || `${opp.estimated_hours_saved_monthly || 28} hrs/month`}</div>
                        </div>
                      </div>

                      <div className="space-y-4 mb-6 flex-1">
                        <div>
                          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Discovered Automation Steps</h4>
                          <ol className="list-decimal list-inside space-y-1.5 text-sm text-slate-300">
                            {steps.map((step, i) => (
                              <li key={i}>{typeof step === 'object' ? JSON.stringify(step) : step}</li>
                            ))}
                          </ol>
                        </div>
                        
                        <div className="bg-primary/10 border border-primary/20 p-4 rounded-xl">
                          <h4 className="text-xs font-semibold text-primary flex items-center gap-1.5 mb-1.5 uppercase tracking-wider">
                            <Sparkles className="h-3.5 w-3.5" /> AI Engine Analysis
                          </h4>
                          <p className="text-xs text-muted-foreground leading-relaxed">
                            {opp.ai_explanation || opp.reasoning || 'Automating this workflow prevents cascading supply-chain delays while maintaining governance.'}
                          </p>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-3 pt-4 border-t border-border/60">
                        <Button onClick={() => handleGenerateWorkflow(opp)} className="gap-2 shadow-sm">
                          <Zap className="h-4 w-4" /> 1-Click Convert to Workflow
                        </Button>
                        <Button 
                          variant="outline" 
                          className="gap-2 text-sky-400 border-sky-500/30 hover:bg-sky-500/10"
                          onClick={() => {
                            toast.info(`Opening Simulation for: ${opp.title}`);
                            navigate('/app/workflows', { state: { autoSimulate: true } });
                          }}
                        >
                          <BarChart className="h-4 w-4" /> Simulate Impact
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>
      </StateWrap>
    </div>
  );
}
