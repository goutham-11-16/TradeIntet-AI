import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '@/lib/api';
import { PageHeader, StateWrap } from '@/components/common';
import { toast } from 'sonner';
import { 
  Sparkles, 
  ArrowDown, 
  Play, 
  Save, 
  Eye, 
  Trash2, 
  AlertTriangle, 
  Info,
  Zap,
  GitBranch,
  Clock,
  ShieldAlert,
  Terminal,
  Database,
  CheckCircle2,
  Send
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';

const TEMPLATES = [
  {
    label: 'Delay Escalation',
    text: 'When a shipment becomes high risk and the expected delay exceeds 2 days, find an alternative route. If the shipment value is above ₹10 lakh, require manager approval before rerouting.'
  },
  {
    label: 'Risk Recovery',
    text: 'If weather risk is severe and shipment contains electronics, reroute immediately. Otherwise, notify the customer about potential delays and monitor.'
  },
  {
    label: 'Customs Monitor',
    text: 'When customs clearance takes more than 48 hours for international shipments, escalate to the compliance team and send a status update to the client.'
  },
  {
    label: 'Delivery Flow',
    text: 'Upon delivery completion, send a satisfaction survey to the customer. If the rating is below 3 stars, create a high-priority support ticket.'
  }
];

const NODE_TYPE_COLORS = {
  trigger: 'border-l-emerald-500 bg-emerald-500/10 text-emerald-400',
  condition: 'border-l-sky-500 bg-sky-500/10 text-sky-400',
  action: 'border-l-purple-500 bg-purple-500/10 text-purple-400',
  approval: 'border-l-amber-500 bg-amber-500/10 text-amber-400',
  delay: 'border-l-yellow-500 bg-yellow-500/10 text-yellow-400',
  notification: 'border-l-blue-500 bg-blue-500/10 text-blue-400',
  end: 'border-l-slate-500 bg-slate-500/10 text-slate-400',
  error: 'border-l-red-500 bg-red-500/10 text-red-400',
  default: 'border-l-slate-500 bg-slate-500/10 text-slate-400'
};

const NODE_ICONS = {
  trigger: <Zap className="w-5 h-5 text-emerald-400" />,
  condition: <GitBranch className="w-5 h-5 text-sky-400" />,
  action: <Terminal className="w-5 h-5 text-purple-400" />,
  approval: <ShieldAlert className="w-5 h-5 text-amber-400" />,
  delay: <Clock className="w-5 h-5 text-yellow-400" />,
  notification: <Send className="w-5 h-5 text-blue-400" />,
  end: <CheckCircle2 className="w-5 h-5 text-slate-400" />,
  error: <AlertTriangle className="w-5 h-5 text-red-400" />,
  default: <Info className="w-5 h-5 text-slate-400" />
};

export default function AutomationCopilot() {
  const [inputText, setInputText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedResult, setGeneratedResult] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [isLoadingWorkflows, setIsLoadingWorkflows] = useState(true);
  
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const promptParam = searchParams.get('prompt');
    if (promptParam) {
      setInputText(promptParam);
    }
    fetchWorkflows();
  }, [searchParams]);

  const fetchWorkflows = async () => {
    setIsLoadingWorkflows(true);
    try {
      const res = await api.workflows();
      const data = res?.data || res;
      setWorkflows(data?.workflows || data || []);
    } catch (err) {
      console.error('Failed to load workflows:', err);
    } finally {
      setIsLoadingWorkflows(false);
    }
  };

  const handleGenerate = async () => {
    if (!inputText.trim()) return;
    setIsGenerating(true);
    setGeneratedResult(null);
    try {
      const res = await api.generateWorkflow({ natural_language: inputText });
      const data = res?.data || res;
      setGeneratedResult(data);
      toast.success('Workflow generated successfully!');
      fetchWorkflows();
    } catch (err) {
      console.error('Failed to generate workflow:', err);
      toast.error(err?.response?.data?.detail || 'Failed to generate workflow');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleViewInStudio = (wf) => {
    const targetWf = wf || generatedResult?.workflow;
    if (!targetWf) return;
    navigate('/app/workflows', { state: { selectedWorkflow: targetWf } });
  };

  const handleSimulate = (wf) => {
    const targetWf = wf || generatedResult?.workflow;
    if (!targetWf) return;
    navigate('/app/workflows', { state: { selectedWorkflow: targetWf, autoSimulate: true } });
  };

  const handleSaveDraft = async () => {
    if (!generatedResult?.workflow) return;
    toast.success(`Workflow '${generatedResult.workflow.name}' saved to VectorDB!`);
    await fetchWorkflows();
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteWorkflow(id);
      toast.success('Workflow deleted');
      fetchWorkflows();
    } catch (err) {
      console.error('Failed to delete workflow:', err);
      toast.error('Failed to delete workflow');
    }
  };

  const handleSeedData = async () => {
    try {
      await api.seedDemoWorkflows();
      toast.success('Demo workflows seeded into VectorDB');
      fetchWorkflows();
    } catch (err) {
      console.error('Failed to seed demo workflows:', err);
    }
  };

  const handleTemplateClick = (text) => {
    setInputText(text);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader 
          title="Automation Copilot" 
          subtitle="Describe what you want to automate in natural language (PS4 AI Automation)" 
        />
        <Button variant="outline" size="sm" onClick={handleSeedData}>
          <Database className="w-4 h-4 mr-2" />
          Seed Demo Data
        </Button>
      </div>

      {/* Main Input Section */}
      <Card className="border-border/60 shadow-md">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            AI Workflow Generator
          </CardTitle>
          <CardDescription>
            Type your process rules and let AI build the automation workflow graph.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea 
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="e.g., When a shipment becomes high risk and the expected delay exceeds 2 days, find an alternative route. If the shipment value is above ₹10 lakh, require manager approval before rerouting."
            className="min-h-[120px] resize-y text-base p-4"
          />
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-muted-foreground self-center mr-2">Templates:</span>
            {TEMPLATES.map((tpl, i) => (
              <Badge 
                key={i} 
                variant="secondary" 
                className="cursor-pointer hover:bg-secondary/80 py-1.5 px-3"
                onClick={() => handleTemplateClick(tpl.text)}
              >
                {tpl.label}
              </Badge>
            ))}
          </div>
          <div className="pt-4 flex justify-end">
            <Button 
              onClick={handleGenerate} 
              disabled={!inputText.trim() || isGenerating}
              className="w-full sm:w-auto"
              size="lg"
            >
              {isGenerating ? (
                <>
                  <Sparkles className="w-4 h-4 mr-2 animate-pulse" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate Workflow
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Generated Result Section */}
      {generatedResult && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          <div className="space-y-6">
            {/* Detected Elements */}
            <Card className="border-border/60">
              <CardHeader>
                <CardTitle className="text-lg">Detected Elements</CardTitle>
                <CardDescription>Structured components extracted by AI Parser</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {generatedResult.detected_trigger && (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider mb-1.5 text-muted-foreground">Trigger Event</div>
                    <Badge className="bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border-emerald-500/30 px-3 py-1 text-sm font-medium">
                      <Zap className="w-3.5 h-3.5 mr-1.5 inline" />
                      {typeof generatedResult.detected_trigger === 'object'
                        ? (generatedResult.detected_trigger.description || generatedResult.detected_trigger.type || JSON.stringify(generatedResult.detected_trigger))
                        : generatedResult.detected_trigger}
                    </Badge>
                  </div>
                )}
                
                {generatedResult.detected_conditions?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider mb-1.5 text-muted-foreground">Evaluated Conditions</div>
                    <div className="flex flex-wrap gap-2">
                      {generatedResult.detected_conditions.map((c, i) => {
                        const label = typeof c === 'object'
                          ? `${c.field || ''} ${c.operator || ''} ${c.value != null ? c.value : ''}${c.unit ? ' ' + c.unit : ''}`.trim() || c.description || JSON.stringify(c)
                          : c;
                        return (
                          <Badge key={i} className="bg-sky-500/20 text-sky-400 hover:bg-sky-500/30 border-sky-500/30 px-3 py-1 text-sm font-medium">
                            <GitBranch className="w-3.5 h-3.5 mr-1.5 inline" />
                            {label}
                          </Badge>
                        );
                      })}
                    </div>
                  </div>
                )}

                {generatedResult.detected_actions?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider mb-1.5 text-muted-foreground">Automated Actions</div>
                    <div className="flex flex-wrap gap-2">
                      {generatedResult.detected_actions.map((a, i) => {
                        const label = typeof a === 'object' ? (a.label || a.tool || JSON.stringify(a)) : a;
                        return (
                          <Badge key={i} className="bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 border-purple-500/30 px-3 py-1 text-sm font-medium">
                            <Terminal className="w-3.5 h-3.5 mr-1.5 inline" />
                            {label}
                          </Badge>
                        );
                      })}
                    </div>
                  </div>
                )}

                {generatedResult.entities?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider mb-1.5 text-muted-foreground">Extracted Entities</div>
                    <div className="flex flex-wrap gap-2">
                      {generatedResult.entities.map((e, i) => (
                        <Badge key={i} variant="outline" className="text-slate-300 border-slate-700 bg-slate-800/50 px-2.5 py-0.5 text-xs">
                          {typeof e === 'object' ? JSON.stringify(e) : e}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* AI Explanation & Warnings */}
            <Card className="border-border/60">
              <CardHeader>
                <CardTitle className="text-lg">AI Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {generatedResult.ai_explanation && (
                  <div className="rounded-lg bg-muted/60 p-4 text-sm border border-border/40">
                    <div className="flex items-center gap-2 mb-2 font-medium text-foreground">
                      <Info className="w-4 h-4 text-sky-400" />
                      Implementation Strategy
                    </div>
                    <p className="text-muted-foreground leading-relaxed">
                      {generatedResult.ai_explanation}
                    </p>
                  </div>
                )}

                {generatedResult.assumptions?.length > 0 && (
                  <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
                    <div className="flex items-center gap-2 mb-2 font-medium text-amber-400">
                      <AlertTriangle className="w-4 h-4" />
                      Assumptions
                    </div>
                    <ul className="list-disc pl-5 space-y-1 text-amber-300/90 text-xs">
                      {generatedResult.assumptions.map((a, i) => (
                        <li key={i}>{typeof a === 'object' ? JSON.stringify(a) : a}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {generatedResult.warnings?.length > 0 && (
                  <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm">
                    <div className="flex items-center gap-2 mb-2 font-medium text-red-400">
                      <ShieldAlert className="w-4 h-4" />
                      Warnings
                    </div>
                    <ul className="list-disc pl-5 space-y-1 text-red-300/90 text-xs">
                      {generatedResult.warnings.map((w, i) => (
                        <li key={i}>{typeof w === 'object' ? JSON.stringify(w) : w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
              <div className="p-6 pt-0 flex gap-3 flex-wrap">
                <Button className="flex-1" onClick={() => handleViewInStudio()}>
                  <Eye className="w-4 h-4 mr-2" />
                  View in Workflow Studio
                </Button>
                <Button variant="secondary" className="flex-1" onClick={() => handleSimulate()}>
                  <Play className="w-4 h-4 mr-2" />
                  Simulate
                </Button>
                <Button variant="outline" className="flex-1" onClick={handleSaveDraft}>
                  <Save className="w-4 h-4 mr-2" />
                  Save as Draft
                </Button>
              </div>
            </Card>
          </div>

          {/* Workflow Preview (Vertical Flow) */}
          <Card className="border-border/60">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Workflow Preview</CardTitle>
                <CardDescription>
                  {generatedResult.workflow?.name || 'Generated logical execution path'}
                </CardDescription>
              </div>
              <Badge variant="outline" className="text-xs">
                {generatedResult.workflow?.nodes?.length || 0} Nodes
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center py-4 space-y-2">
                {generatedResult.workflow?.nodes?.map((node, index) => {
                  const nodeTypeKey = (node.type || 'default').toLowerCase();
                  const styleClass = NODE_TYPE_COLORS[nodeTypeKey] || NODE_TYPE_COLORS.default;
                  const icon = NODE_ICONS[nodeTypeKey] || NODE_ICONS.default;
                  const isLast = index === generatedResult.workflow.nodes.length - 1;

                  return (
                    <React.Fragment key={node.id || index}>
                      <div className={`w-full max-w-md rounded-lg border p-4 shadow-sm border-l-4 ${styleClass} bg-card text-foreground flex items-start gap-4 transition-all hover:border-border`}>
                        <div className="mt-0.5 p-1.5 rounded-md bg-background/80 shadow-sm border border-border/40">
                          {icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="font-semibold text-sm truncate">{node.label}</h4>
                            <Badge variant="outline" className="text-[10px] uppercase tracking-wider py-0 px-1.5 text-muted-foreground">
                              {node.type}
                            </Badge>
                          </div>
                          {node.description && (
                            <p className="text-xs text-muted-foreground">{node.description}</p>
                          )}
                          {node.tool && (
                            <p className="text-[11px] text-purple-400 font-mono mt-1">Tool: {node.tool}</p>
                          )}
                        </div>
                      </div>
                      
                      {!isLast && (
                        <div className="flex flex-col items-center py-1">
                          <div className="w-px h-5 bg-border/80"></div>
                          <ArrowDown className="w-4 h-4 text-muted-foreground -mt-1" />
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}

                {(!generatedResult.workflow?.nodes || generatedResult.workflow.nodes.length === 0) && (
                  <div className="text-center py-10 text-muted-foreground">
                    <GitBranch className="w-10 h-10 mx-auto mb-3 opacity-20" />
                    <p>No valid nodes generated.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Saved Workflows Section */}
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Save className="w-5 h-5 text-muted-foreground" />
            Active & Saved Workflows ({workflows.length})
          </CardTitle>
          <CardDescription>Persistent automation workflows stored in VectorDB</CardDescription>
        </CardHeader>
        <CardContent>
          <StateWrap isLoading={isLoadingWorkflows} isEmpty={workflows.length === 0}>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {workflows.map((wf) => (
                <div key={wf._id || wf.id} className="border border-border/60 rounded-lg p-4 bg-card/50 hover:bg-card transition-colors flex flex-col h-full shadow-sm">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-semibold truncate pr-2">{wf.name || 'Untitled Workflow'}</h3>
                    <Badge variant={wf.status === 'active' ? 'default' : 'secondary'} className="capitalize">
                      {wf.status || 'draft'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-4 flex-1">
                    {wf.description || wf.natural_language || 'No description provided.'}
                  </p>
                  <div className="flex items-center gap-2 pt-3 border-t border-border/50">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="flex-1 text-xs h-8"
                      onClick={() => handleViewInStudio(wf)}
                    >
                      <Eye className="w-3.5 h-3.5 mr-1.5" />
                      View
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="flex-1 text-xs h-8 text-sky-400 hover:text-sky-300"
                      onClick={() => handleSimulate(wf)}
                    >
                      <Play className="w-3.5 h-3.5 mr-1.5" />
                      Simulate
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-500/10"
                      onClick={() => handleDelete(wf._id || wf.id)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </StateWrap>
        </CardContent>
      </Card>
    </div>
  );
}
