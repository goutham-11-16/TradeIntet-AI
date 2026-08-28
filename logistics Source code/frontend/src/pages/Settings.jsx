import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader, StateWrap } from "@/components/common";
import { User, Bell, SlidersHorizontal, Users, ScrollText, Loader2, Trash2, Mail } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";

const inputCls = "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary";

function ProfileTab() {
  const { user, refresh } = useAuth();
  const [form, setForm] = useState({ name: user?.name || "", phone: user?.phone || "", organization: user?.organization || "" });
  const [saving, setSaving] = useState(false);
  const save = async () => {
    setSaving(true);
    try { await api.updateProfile(form); toast.success("Profile updated"); await refresh(); }
    catch { toast.error("Update failed"); } finally { setSaving(false); }
  };
  return (
    <div className="max-w-lg space-y-4" data-testid="profile-tab">
      <label className="block text-sm">Full name<input data-testid="profile-name" className={inputCls} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
      <label className="block text-sm">Email<input className={`${inputCls} opacity-60`} value={user?.email} disabled /></label>
      <label className="block text-sm">Phone<input data-testid="profile-phone" className={inputCls} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
      <label className="block text-sm">Organization<input data-testid="profile-org" className={inputCls} value={form.organization} onChange={(e) => setForm({ ...form, organization: e.target.value })} /></label>
      <button data-testid="save-profile" onClick={save} disabled={saving} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">{saving && <Loader2 className="h-4 w-4 animate-spin" />} Save Profile</button>
    </div>
  );
}

function PrefsTab() {
  const qc = useQueryClient();
  const { canManage } = useAuth();
  const { data, isLoading } = useQuery({ queryKey: ["prefs"], queryFn: () => api.getPrefs().then((r) => r.data) });
  const [prefs, setPrefs] = useState(null);
  useEffect(() => { if (data) setPrefs(data); }, [data]);
  const save = async (next) => {
    setPrefs(next);
    try { await api.setPrefs(next); qc.invalidateQueries({ queryKey: ["prefs"] }); } catch { toast.error("Save failed"); }
  };
  if (isLoading || !prefs) return <StateWrap loading />;
  const toggles = [["email_alerts", "Email alerts"], ["auto_email", "Auto-email on risk threshold / ETA shift"], ["critical_alerts", "Critical alerts"], ["risk_alerts", "Risk alerts"], ["eta_changes", "ETA change alerts"]];
  const sendTest = async () => {
    try { const { data } = await api.testEmail(); toast.success(`Test email sent to ${data.recipient}`); }
    catch (e) { toast.error(e.response?.data?.detail || "Email failed"); }
  };
  return (
    <div className="max-w-lg space-y-5" data-testid="prefs-tab">
      {canManage() && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">Email Delivery</h3>
          <label className="block text-sm">Alert recipient email
            <input data-testid="pref-recipient" type="email" className={inputCls} value={prefs.alert_recipient || ""} onChange={(e) => setPrefs({ ...prefs, alert_recipient: e.target.value })} onBlur={() => save(prefs)} placeholder="manager@company.com" /></label>
          <button data-testid="send-test-email" onClick={sendTest} className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-accent"><Mail className="h-4 w-4" /> Send Test Email</button>
        </div>
      )}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold">Notifications</h3>
        {toggles.map(([k, l]) => (
          <div key={k} className="flex items-center justify-between rounded-md border border-border/60 px-3 py-2">
            <span className="text-sm">{l}</span>
            <Switch data-testid={`pref-${k}`} checked={!!prefs[k]} onCheckedChange={(v) => save({ ...prefs, [k]: v })} />
          </div>
        ))}
      </div>
      <div className="space-y-3">
        <h3 className="text-sm font-semibold">Risk Settings</h3>
        <label className="block text-sm">Risk threshold: {prefs.risk_threshold}
          <input data-testid="pref-threshold" type="range" min="0" max="100" value={prefs.risk_threshold} onChange={(e) => setPrefs({ ...prefs, risk_threshold: Number(e.target.value) })} onMouseUp={(e) => save({ ...prefs, risk_threshold: Number(e.target.value) })} className="w-full accent-primary" /></label>
        <label className="block text-sm">Alert sensitivity
          <select data-testid="pref-sensitivity" className={inputCls} value={prefs.alert_sensitivity} onChange={(e) => save({ ...prefs, alert_sensitivity: e.target.value })}>{["Low", "Medium", "High"].map((s) => <option key={s}>{s}</option>)}</select></label>
      </div>
    </div>
  );
}

function UsersTab() {
  const qc = useQueryClient();
  const { user } = useAuth();
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["admin-users"], queryFn: () => api.adminUsers().then((r) => r.data) });
  const roleMut = useMutation({ mutationFn: ({ id, role }) => api.updateRole(id, role), onSuccess: () => { toast.success("Role updated"); qc.invalidateQueries({ queryKey: ["admin-users"] }); }, onError: (e) => toast.error(e.response?.data?.detail || "Failed") });
  const delMut = useMutation({ mutationFn: (id) => api.deleteUser(id), onSuccess: () => { toast.success("User deleted"); qc.invalidateQueries({ queryKey: ["admin-users"] }); }, onError: (e) => toast.error(e.response?.data?.detail || "Failed") });
  return (
    <StateWrap loading={isLoading} error={error ? "Failed to load users." : null} onRetry={refetch}>
      {data && (
        <div className="overflow-x-auto"><table className="w-full text-sm" data-testid="users-table"><thead className="border-b border-border/60 text-left text-xs uppercase text-muted-foreground"><tr><th className="px-3 py-2">Name</th><th className="px-3 py-2">Email</th><th className="px-3 py-2">Organization</th><th className="px-3 py-2">Role</th><th className="px-3 py-2"></th></tr></thead>
          <tbody>{data.users.map((u) => (
            <tr key={u.id} className="border-b border-border/40"><td className="px-3 py-2 font-semibold">{u.name}</td><td className="px-3 py-2 text-muted-foreground">{u.email}</td><td className="px-3 py-2">{u.organization}</td>
              <td className="px-3 py-2"><select data-testid={`role-${u.id}`} value={u.role} onChange={(e) => roleMut.mutate({ id: u.id, role: e.target.value })} className="rounded-md border border-border bg-background px-2 py-1 text-xs"><option value="admin">admin</option><option value="manager">manager</option><option value="viewer">viewer</option></select></td>
              <td className="px-3 py-2">{u.email !== user.email && <button data-testid={`deluser-${u.id}`} onClick={() => delMut.mutate(u.id)} className="rounded p-1.5 text-red-500 hover:bg-red-500/10"><Trash2 className="h-4 w-4" /></button>}</td>
            </tr>
          ))}</tbody>
        </table></div>
      )}
    </StateWrap>
  );
}

function AuditTab() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["audit"], queryFn: () => api.auditLogs().then((r) => r.data) });
  return (
    <StateWrap loading={isLoading} error={error ? "Failed to load audit logs." : null} onRetry={refetch}>
      {data && (
        <div className="max-h-[500px] overflow-auto"><table className="w-full text-sm" data-testid="audit-table"><thead className="sticky top-0 border-b border-border/60 bg-card text-left text-xs uppercase text-muted-foreground"><tr><th className="px-3 py-2">Time</th><th className="px-3 py-2">Actor</th><th className="px-3 py-2">Action</th><th className="px-3 py-2">Detail</th></tr></thead>
          <tbody>{data.logs.map((l) => (<tr key={l.id} className="border-b border-border/40"><td className="px-3 py-2 font-mono text-xs text-muted-foreground">{new Date(l.created_at).toLocaleString()}</td><td className="px-3 py-2">{l.actor}</td><td className="px-3 py-2 font-mono text-xs">{l.action}</td><td className="px-3 py-2 text-muted-foreground">{l.detail}</td></tr>))}</tbody>
        </table></div>
      )}
    </StateWrap>
  );
}

export default function Settings() {
  const { hasRole } = useAuth();
  const isAdmin = hasRole("admin");
  return (
    <>
      <PageHeader testId="settings-header" title="Settings" subtitle="Profile, notifications, risk thresholds & administration" />
      <Tabs defaultValue="profile">
        <TabsList className="flex-wrap">
          <TabsTrigger value="profile" data-testid="tab-profile"><User className="mr-2 h-4 w-4" /> Profile</TabsTrigger>
          <TabsTrigger value="prefs" data-testid="tab-prefs"><Bell className="mr-2 h-4 w-4" /> Notifications & Risk</TabsTrigger>
          {isAdmin && <TabsTrigger value="users" data-testid="tab-users"><Users className="mr-2 h-4 w-4" /> Users</TabsTrigger>}
          {isAdmin && <TabsTrigger value="audit" data-testid="tab-audit"><ScrollText className="mr-2 h-4 w-4" /> Audit Logs</TabsTrigger>}
        </TabsList>
        <div className="mt-6 rounded-xl border border-border/60 bg-card p-5">
          <TabsContent value="profile"><ProfileTab /></TabsContent>
          <TabsContent value="prefs"><PrefsTab /></TabsContent>
          {isAdmin && <TabsContent value="users"><UsersTab /></TabsContent>}
          {isAdmin && <TabsContent value="audit"><AuditTab /></TabsContent>}
        </div>
      </Tabs>
    </>
  );
}
