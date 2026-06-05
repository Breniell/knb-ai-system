import { useQuery } from "@tanstack/react-query";
import { ArrowRight, FolderKanban, ListChecks, Workflow, Sparkles, GraduationCap } from "lucide-react";

import { getAnalytics } from "../../features/api";
import { AGENTS, POLES } from "../../design/agents";
import { useAuth } from "../../auth/AuthProvider";
import { useUiStore } from "../../state/uiStore";
import { AgentAvatar, PageHeader, StatCard } from "../components/primitives";

export function DashboardPage() {
  const { user } = useAuth();
  const setPage = useUiStore((s) => s.setPage);
  const analytics = useQuery({ queryKey: ["analytics"], queryFn: async () => (await getAnalytics()).metrics });
  const m = analytics.data;
  const firstName = (user?.displayName || user?.email || "").split(/[@ ]/)[0] || "bienvenue";

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Tableau de bord"
        title={`Bonjour, ${firstName}`}
        subtitle="Votre équipe d'agents IA est prête. Lancez un workflow complet ou discutez avec un spécialiste."
        actions={
          <>
            <button onClick={() => setPage("console")} className="btn-outline"><Workflow size={16} />Workflow</button>
            <button onClick={() => setPage("agents")} className="btn-primary"><Sparkles size={16} />Parler à un agent</button>
          </>
        }
      />

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard icon={FolderKanban} label="Projets" value={analytics.isLoading ? "—" : m?.projects ?? 0} hint="dossiers clients actifs" />
        <StatCard icon={ListChecks} label="Tâches" value={analytics.isLoading ? "—" : m?.tasks ?? 0} hint="à suivre et livrer" accent="text-clay-500" />
        <StatCard icon={Workflow} label="Exécutions IA" value={analytics.isLoading ? "—" : m?.executions ?? 0} hint="workflows multi-agents" accent="text-info" />
      </div>

      {/* Quick launch row */}
      <div className="grid gap-4 md:grid-cols-3">
        <QuickCard onClick={() => setPage("console")} icon={Workflow} title="Lancer un projet complet"
          text="Le planificateur découpe la demande et orchestre les bons spécialistes, de la conception à la revue." />
        <QuickCard onClick={() => setPage("agents")} icon={Sparkles} title="Consulter un expert"
          text="Discutez en direct avec l'un des 16 agents : devis, code, design, marketing, finance…" />
        <QuickCard onClick={() => setPage("formation")} icon={GraduationCap} title="Former vos agents"
          text="Assignez des cours et des sources web pour que vos agents montent en compétence en continu." />
      </div>

      {/* Agents overview */}
      <section className="card p-6">
        <div className="mb-5 flex items-end justify-between">
          <div>
            <div className="eyebrow mb-1">Votre équipe</div>
            <h2 className="text-lg font-bold text-ink">16 agents, 5 pôles</h2>
          </div>
          <button onClick={() => setPage("agents")} className="btn-ghost btn-sm">Tout voir <ArrowRight size={14} /></button>
        </div>
        <div className="space-y-5">
          {POLES.map((pole) => {
            const list = AGENTS.filter((a) => a.pole === pole);
            return (
              <div key={pole}>
                <div className="mb-2 text-xs font-semibold text-muted">{pole}</div>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
                  {list.map((a) => (
                    <button
                      key={a.id}
                      onClick={() => setPage("agents")}
                      className="flex items-center gap-2.5 rounded-xl border border-line bg-surface px-3 py-2.5 text-left transition-all hover:border-line-strong hover:shadow-card"
                    >
                      <AgentAvatar agentKey={a.id} size="sm" />
                      <span className="truncate text-[13px] font-medium text-ink-soft">{a.role}</span>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function QuickCard({ onClick, icon: Icon, title, text }: { onClick: () => void; icon: typeof Workflow; title: string; text: string }) {
  return (
    <button onClick={onClick} className="card group flex flex-col items-start p-5 text-left transition-all hover:-translate-y-0.5 hover:shadow-lift">
      <span className="mb-3 grid h-10 w-10 place-items-center rounded-xl bg-brand-600/10 text-brand-700 ring-1 ring-brand-600/15">
        <Icon size={19} strokeWidth={1.9} />
      </span>
      <div className="font-display text-[15px] font-semibold text-ink">{title}</div>
      <p className="mt-1.5 text-sm text-muted">{text}</p>
      <span className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-brand-700 opacity-0 transition-opacity group-hover:opacity-100">
        Ouvrir <ArrowRight size={14} />
      </span>
    </button>
  );
}
