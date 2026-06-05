import type { FormEvent, ReactNode } from "react";
import { useState } from "react";
import { ArrowRight, Sparkles, ShieldCheck, Workflow } from "lucide-react";

import { useAuth } from "../../auth/AuthProvider";

/* Shared split-screen auth layout (brand panel + form) */
export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-brand-800 p-12 text-white lg:flex">
        <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-brand-500/30 blur-3xl" />
        <div className="absolute -bottom-32 -left-16 h-96 w-96 rounded-full bg-clay-500/20 blur-3xl" />
        <div className="relative flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-white/15 font-display text-2xl font-bold backdrop-blur">K</span>
          <div><div className="font-display text-lg font-bold">KNB AI</div><div className="text-xs text-white/70">Yaoundé · Cameroun</div></div>
        </div>
        <div className="relative">
          <h2 className="max-w-md font-display text-3xl font-bold leading-tight">Une agence digitale entière, augmentée par l'IA.</h2>
          <p className="mt-3 max-w-md text-sm text-white/80">16 agents spécialisés produisent devis, code, design, contenus et plans projet — du brief au livrable.</p>
          <div className="mt-8 space-y-3">
            {[[Sparkles, "16 experts à la demande"], [Workflow, "Workflows multi-agents orchestrés"], [ShieldCheck, "Revue qualité automatique"]].map(([Icon, t], i) => (
              <div key={i} className="flex items-center gap-3 text-sm text-white/90">
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-white/10"><Icon size={16} /></span>{t as string}
              </div>
            ))}
          </div>
        </div>
        <div className="relative text-xs text-white/50">© {new Date().getFullYear()} KNB Dev Solutions</div>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <div className="font-display text-2xl font-bold brand-gradient-text">KNB AI</div>
          </div>
          <h1 className="font-display text-2xl font-bold text-ink">{title}</h1>
          <p className="mb-7 mt-1 text-sm text-muted">{subtitle}</p>
          {children}
        </div>
      </div>
    </main>
  );
}

export function RegisterPage({ onSwitchToLogin }: { onSwitchToLogin: () => void }) {
  const { register } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null); setSubmitting(true);
    try { await register(email, password, displayName || undefined); }
    catch (err) { setError(err instanceof Error ? err.message : "Impossible de créer le compte"); }
    finally { setSubmitting(false); }
  }

  return (
    <AuthShell title="Créer un compte" subtitle="Rejoignez votre espace KNB AI System.">
      <form onSubmit={submit} className="space-y-4">
        <label className="block">
          <span className="label">Nom d'affichage</span>
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="field mt-1.5" placeholder="Votre nom" />
        </label>
        <label className="block">
          <span className="label">Adresse e-mail</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="field mt-1.5" placeholder="vous@exemple.com" required />
        </label>
        <label className="block">
          <span className="label">Mot de passe</span>
          <input type="password" minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} className="field mt-1.5" placeholder="Min. 6 caractères" required />
        </label>
        {error && <div className="rounded-lg border border-danger/25 bg-danger/[0.05] px-3 py-2.5 text-sm text-danger">{error}</div>}
        <button type="submit" disabled={submitting} className="btn-primary w-full">{submitting ? "Création…" : "Créer le compte"}<ArrowRight size={15} /></button>
      </form>
      <button onClick={onSwitchToLogin} className="mt-5 w-full text-center text-sm text-muted hover:text-ink">
        Déjà un compte ? <span className="font-semibold text-brand-700">Se connecter</span>
      </button>
    </AuthShell>
  );
}
