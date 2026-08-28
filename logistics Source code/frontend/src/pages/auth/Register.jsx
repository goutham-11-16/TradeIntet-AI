import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import AuthShell, { Field, inputCls } from "./AuthShell";
import { useAuth, formatApiError } from "@/context/AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "", organization: "", email: "", phone: "", password: "", confirm: "", role: "manager",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.name || !form.organization || !form.email || !form.password) { setError("Please fill all required fields."); return; }
    if (form.password.length < 6) { setError("Password must be at least 6 characters."); return; }
    if (form.password !== form.confirm) { setError("Passwords do not match."); return; }
    setLoading(true);
    try {
      const { confirm, ...payload } = form;
      const u = await register(payload);
      toast.success(`Account created. Welcome, ${u.name}`);
      navigate("/app/dashboard");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Create your account" subtitle="Set up your logistics resilience workspace"
      footer={<>Already registered? <Link to="/login" className="font-semibold text-primary hover:underline" data-testid="link-login">Sign in</Link></>}>
      <form onSubmit={submit} className="space-y-4" data-testid="register-form">
        {error && <div data-testid="register-error" className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500">{error}</div>}
        <div className="grid grid-cols-2 gap-3">
          <Field label="Full name"><input data-testid="reg-name" className={inputCls} value={form.name} onChange={set("name")} placeholder="Jane Doe" /></Field>
          <Field label="Organization"><input data-testid="reg-org" className={inputCls} value={form.organization} onChange={set("organization")} placeholder="Acme Logistics" /></Field>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Email"><input data-testid="reg-email" type="email" className={inputCls} value={form.email} onChange={set("email")} placeholder="you@company.com" /></Field>
          <Field label="Phone"><input data-testid="reg-phone" className={inputCls} value={form.phone} onChange={set("phone")} placeholder="+1 555 000" /></Field>
        </div>
        <Field label="Role">
          <select data-testid="reg-role" className={inputCls} value={form.role} onChange={set("role")}>
            <option value="manager">Logistics Manager</option>
            <option value="viewer">Viewer</option>
            <option value="admin">Admin</option>
          </select>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Password"><input data-testid="reg-password" type="password" className={inputCls} value={form.password} onChange={set("password")} placeholder="••••••••" /></Field>
          <Field label="Confirm password"><input data-testid="reg-confirm" type="password" className={inputCls} value={form.confirm} onChange={set("confirm")} placeholder="••••••••" /></Field>
        </div>
        <button data-testid="register-submit" disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60">
          {loading && <Loader2 className="h-4 w-4 animate-spin" />} Create account
        </button>
      </form>
    </AuthShell>
  );
}
