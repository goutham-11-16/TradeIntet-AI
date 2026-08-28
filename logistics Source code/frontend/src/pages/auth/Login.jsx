import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import AuthShell, { Field, inputCls } from "./AuthShell";
import { useAuth, formatApiError } from "@/context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "admin", password: "admin123", remember: true });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.email || !form.password) { setError("Username/Email and password are required."); return; }
    setLoading(true);
    try {
      const u = await login(form);
      toast.success(`Welcome back, ${u.name}`);
      navigate("/app/dashboard");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  const quick = (email, password) => setForm({ email, password, remember: true });

  return (
    <AuthShell title="Sign in" subtitle="Access your logistics command center"
      footer={<>Need help? Contact system administrator</>}>
      <form onSubmit={submit} className="space-y-4" data-testid="login-form">
        {error && <div data-testid="login-error" className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500">{error}</div>}
        <Field label="Username / Email">
          <input data-testid="login-email" type="text" className={inputCls} value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="admin" />
        </Field>
        <Field label="Password">
          <input data-testid="login-password" type="password" className={inputCls} value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="admin123" />
        </Field>
        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-muted-foreground">
            <input type="checkbox" data-testid="login-remember" checked={form.remember}
              onChange={(e) => setForm({ ...form, remember: e.target.checked })} className="h-4 w-4 rounded border-border" />
            Remember me
          </label>
        </div>
        <button data-testid="login-submit" disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60">
          {loading && <Loader2 className="h-4 w-4 animate-spin" />} Sign in
        </button>
      </form>
      <div className="mt-6 rounded-md border border-border/60 bg-card p-3.5 text-xs">
        <p className="mb-2 font-semibold text-muted-foreground">Single Admin Login:</p>
        <button type="button" data-testid="quick-admin" onClick={() => quick("admin", "admin123")}
          className="flex w-full items-center justify-between rounded-md border border-primary/40 bg-primary/10 px-3 py-2 text-left font-medium hover:bg-primary/20 transition-colors">
          <span className="font-semibold text-primary">Administrator</span>
          <span className="font-mono text-muted-foreground">admin / admin123</span>
        </button>
      </div>
    </AuthShell>
  );
}
