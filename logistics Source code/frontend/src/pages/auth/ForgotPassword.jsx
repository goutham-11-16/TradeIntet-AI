import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import AuthShell, { Field, inputCls } from "./AuthShell";
import { api, formatApiError } from "@/lib/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.forgot({ email });
      setSent(data.debug_token || true);
      toast.success("Reset link generated");
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Forgot password" subtitle="We'll send a reset link to your email"
      footer={<Link to="/login" className="font-semibold text-primary hover:underline" data-testid="link-back-login">Back to sign in</Link>}>
      {sent ? (
        <div data-testid="forgot-success" className="space-y-4">
          <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-500">
            If that email exists, a reset link has been sent. (Check server logs for the demo link.)
          </div>
          {typeof sent === "string" && (
            <Link to={`/reset-password?token=${sent}`} data-testid="forgot-demo-link"
              className="block rounded-md border border-primary/30 bg-primary/10 px-4 py-3 text-center text-sm font-semibold text-primary hover:bg-primary/20">
              Continue to reset password (demo)
            </Link>
          )}
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4" data-testid="forgot-form">
          <Field label="Email">
            <input data-testid="forgot-email" type="email" className={inputCls} value={email}
              onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" required />
          </Field>
          <button data-testid="forgot-submit" disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />} Send reset link
          </button>
        </form>
      )}
    </AuthShell>
  );
}
