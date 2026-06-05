import type { FormEvent } from "react";
import { useState } from "react";
import { ArrowRight } from "lucide-react";

import { useAuth } from "../../auth/AuthProvider";
import { AuthShell } from "./RegisterPage";

export function LoginPage({ onSwitchToRegister }: { onSwitchToRegister: () => void }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null); setSubmitting(true);
    try { await login(email, password); }
    catch (err) { setError(err instanceof Error ? err.message : "Identifiants invalides"); }
    finally { setSubmitting(false); }
  }

  return (
    <AuthShell title="Connexion" subtitle="Accédez à votre espace KNB AI System.">
      <form onSubmit={submit} className="space-y-4">
        <label className="block">
          <span className="label">Adresse e-mail</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="field mt-1.5" placeholder="vous@exemple.com" required />
        </label>
        <label className="block">
          <span className="label">Mot de passe</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="field mt-1.5" placeholder="••••••••" required />
        </label>
        {error && <div className="rounded-lg border border-danger/25 bg-danger/[0.05] px-3 py-2.5 text-sm text-danger">{error}</div>}
        <button type="submit" disabled={submitting} className="btn-primary w-full">{submitting ? "Connexion…" : "Se connecter"}<ArrowRight size={15} /></button>
      </form>
      <button onClick={onSwitchToRegister} className="mt-5 w-full text-center text-sm text-muted hover:text-ink">
        Pas encore de compte ? <span className="font-semibold text-brand-700">Créer un compte</span>
      </button>
    </AuthShell>
  );
}
