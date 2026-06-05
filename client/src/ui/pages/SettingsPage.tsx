import { LogOut, User, Plug, Cpu } from "lucide-react";

import { useAuth } from "../../auth/AuthProvider";
import { env } from "../../config/env";
import { PageHeader } from "../components/primitives";

function Section({ icon: Icon, title, children }: { icon: typeof User; title: string; children: React.ReactNode }) {
  return (
    <section className="card p-5">
      <div className="mb-4 flex items-center gap-2"><Icon size={16} className="text-brand-600" /><h3 className="font-display text-sm font-semibold text-ink">{title}</h3></div>
      {children}
    </section>
  );
}
function Row({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between border-b border-line py-2.5 last:border-0">
      <span className="text-sm text-muted">{label}</span>
      <span className={`text-sm text-ink-soft ${mono ? "font-mono text-xs" : ""}`}>{value}</span>
    </div>
  );
}

export function SettingsPage() {
  const { user, logout } = useAuth();
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Système" title="Paramètres" subtitle="Configuration de la plateforme KNB AI System." />

      <Section icon={User} title="Profil">
        <Row label="E-mail" value={user?.email ?? "mode local"} />
        <Row label="Nom" value={user?.displayName ?? "—"} />
        <Row label="UID" value={user?.uid ?? "—"} mono />
        <div className="pt-3"><button onClick={() => void logout()} className="btn-danger"><LogOut size={15} />Se déconnecter</button></div>
      </Section>

      <Section icon={Plug} title="Endpoints">
        <Row label="Serveur API" value={env.apiUrl} mono />
        <Row label="Firebase Project" value={env.firebase.projectId || "non configuré"} mono />
        <Row label="Auth Domain" value={env.firebase.authDomain || "non configuré"} mono />
      </Section>

      <Section icon={Cpu} title="Fournisseurs IA">
        <div className="space-y-2">
          {[
            { name: "Groq", models: "llama-3.3-70b", status: "Principal", tone: "border-brand-600/25 bg-brand-600/[0.08] text-brand-700" },
            { name: "Gemini", models: "gemini-2.0-flash + embeddings", status: "Secondaire", tone: "border-line bg-surface text-muted" },
            { name: "Mistral", models: "mistral-small", status: "Secondaire", tone: "border-line bg-surface text-muted" },
            { name: "OpenRouter", models: "multi-modèles", status: "Fallback", tone: "border-line bg-surface text-muted" },
          ].map((p) => (
            <div key={p.name} className="flex items-center justify-between rounded-xl border border-line bg-surface-2/40 px-4 py-3">
              <div><div className="text-sm font-medium text-ink">{p.name}</div><div className="text-xs text-faint">{p.models}</div></div>
              <span className={`badge ${p.tone}`}>{p.status}</span>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-faint">Les clés API se configurent dans le fichier <span className="font-mono">.env</span> du serveur.</p>
      </Section>

      <Section icon={Cpu} title="À propos">
        <Row label="Version" value="2.0.0 — refonte" />
        <Row label="Architecture" value="Multi-agents LangGraph" />
        <Row label="Agents" value="16 spécialistes, 5 pôles" />
        <Row label="Mémoire" value="Firestore + Qdrant (vecteurs)" />
      </Section>
    </div>
  );
}
