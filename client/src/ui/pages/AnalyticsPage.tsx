import { useQuery } from "@tanstack/react-query";
import { FolderKanban, ListChecks, Workflow, BarChart3 } from "lucide-react";

import { getAnalytics } from "../../features/api";
import { PageHeader, StatCard } from "../components/primitives";

export function AnalyticsPage() {
  const query = useQuery({ queryKey: ["analytics"], queryFn: async () => (await getAnalytics()).metrics, refetchInterval: 30000 });
  const m = query.data;
  const v = (n?: number) => (query.isLoading ? "—" : n ?? 0);

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Système" title="Analytics" subtitle="Vue d'ensemble de l'activité de la plateforme." />
      {query.isError && <div className="card border-danger/25 bg-danger/[0.04] p-5 text-sm text-danger">Impossible de charger les analytics.</div>}

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard icon={FolderKanban} label="Projets" value={v(m?.projects)} hint="dossiers créés" />
        <StatCard icon={ListChecks} label="Tâches" value={v(m?.tasks)} hint="tâches enregistrées" accent="text-clay-500" />
        <StatCard icon={Workflow} label="Exécutions IA" value={v(m?.executions)} hint="workflows lancés" accent="text-info" />
      </div>

      <section className="card p-5">
        <div className="mb-4 flex items-center gap-2"><BarChart3 size={16} className="text-brand-600" /><h3 className="font-display text-sm font-semibold text-ink">Activité récente</h3></div>
        <div className="flex items-center justify-center rounded-xl border border-dashed border-line bg-surface-2/30 py-12 text-center text-sm text-faint">
          Les graphiques d'activité détaillés arrivent prochainement.
        </div>
      </section>
    </div>
  );
}
