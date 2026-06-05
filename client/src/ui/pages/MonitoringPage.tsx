import { useQuery } from "@tanstack/react-query";
import { Activity, Server } from "lucide-react";

import { getAiMetrics, getServiceStatus } from "../../features/api";
import { PageHeader, Skeleton } from "../components/primitives";

const SERVICE_TONE: Record<string, string> = {
  UP: "border-brand-600/25 bg-brand-600/[0.08] text-brand-700",
  DOWN: "border-danger/25 bg-danger/[0.06] text-danger",
  DEGRADED: "border-clay-500/25 bg-clay-500/10 text-clay-700",
};
const METRIC_LABELS: Record<string, string> = {
  total_workflows: "Workflows", active_agents: "Agents actifs", avg_execution_time: "Temps moyen",
  success_rate: "Taux de succès", errors_last_hour: "Erreurs (1h)", memory_usage_mb: "Mémoire (Mo)",
};

export function MonitoringPage() {
  const status = useQuery({ queryKey: ["service-status"], queryFn: getServiceStatus, refetchInterval: 10000 });
  const metrics = useQuery({ queryKey: ["ai-metrics"], queryFn: getAiMetrics, refetchInterval: 10000 });
  const services = status.data?.services ?? {};
  const aiMetrics = metrics.data?.metrics ?? {};

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Système"
        title="Monitoring"
        subtitle={status.data?.timestamp ? `Mise à jour : ${new Date(status.data.timestamp).toLocaleTimeString("fr-FR")}` : "Actualisation toutes les 10 secondes"}
        actions={
          <span className={`badge ${status.isError ? "border-danger/25 bg-danger/[0.06] text-danger" : "border-brand-600/20 bg-brand-600/[0.08] text-brand-700"}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${status.isError ? "bg-danger" : "animate-pulse bg-brand-500"}`} />{status.isError ? "Déconnecté" : "En direct"}
          </span>
        }
      />

      {status.isError && <div className="card border-danger/25 bg-danger/[0.04] p-4 text-sm text-danger">Impossible de contacter le serveur.</div>}

      <section className="card p-5">
        <div className="mb-4 flex items-center gap-2"><Server size={16} className="text-brand-600" /><h3 className="font-display text-sm font-semibold text-ink">Services infrastructure</h3></div>
        {status.isLoading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)}</div>
        ) : Object.keys(services).length === 0 ? (
          <p className="py-4 text-center text-sm text-faint">Aucune donnée de service.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(services).map(([name, st]) => (
              <div key={name} className="rounded-xl border border-line bg-surface-2/40 p-4">
                <div className="flex items-center justify-between">
                  <span className="eyebrow">{name}</span>
                  <span className={`badge ${SERVICE_TONE[st] ?? "border-line bg-surface text-muted"}`}>{st}</span>
                </div>
                <div className="mt-2 text-xs text-muted">{st === "UP" ? "Opérationnel" : st === "DOWN" ? "Hors service" : "Dégradé"}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="card p-5">
        <div className="mb-4 flex items-center gap-2"><Activity size={16} className="text-brand-600" /><h3 className="font-display text-sm font-semibold text-ink">Métriques IA</h3></div>
        {metrics.isLoading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-16" />)}</div>
        ) : metrics.isError ? (
          <p className="py-4 text-center text-sm text-faint">Service IA inaccessible (port 8000).</p>
        ) : Object.keys(aiMetrics).length === 0 ? (
          <p className="py-4 text-center text-sm text-faint">Aucune métrique disponible.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(aiMetrics).map(([k, v]) => (
              <div key={k} className="rounded-xl border border-line bg-surface-2/40 p-4">
                <div className="eyebrow">{METRIC_LABELS[k] ?? k}</div>
                <div className="mt-1 font-display text-2xl font-bold tabular-nums text-ink">{v}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
