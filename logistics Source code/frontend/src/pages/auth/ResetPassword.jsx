import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import AuthShell, { Field, inputCls } from "./AuthShell";
import { api, formatApiError } from "@/lib/api";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") || "";
  const [form, setForm] = useState({ password: "", confirm: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 6) { setError("Password must be at least 6 characters."); return; }
    if (form.password !== form.confirm) { setError("Passwords do not match."); return; }
    setLoading(true);
    try {
      await api.reset({ token, password: form.password });
      toast.success("Password reset. Please sign in.");
      navigate("/login");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Reset password" subtitle="Choose a new password for your account"
      footer={<Link to="/login" className="font-semibold text-primary hover:underline">Back to sign in</Link>}>
      {!token ? (
        <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500" data-testid="reset-no-token">
          Missing or invalid reset token. Please request a new link.
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4" data-testid="reset-form">
          {error && <div data-testid="reset-error" className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500">{error}</div>}
          <Field label="New password"><input data-testid="reset-password" type="password" className={inputCls} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="••••••••" /></Field>
          <Field label="Confirm password"><input data-testid="reset-confirm" type="password" className={inputCls} value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} placeholder="••••••••" /></Field>
          <button data-testid="reset-submit" disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />} Reset password
          </button>
        </form>
      )}
    </AuthShell>
  );
}
