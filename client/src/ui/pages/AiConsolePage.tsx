import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Play, CheckCircle2, XCircle, Clock, History, FileStack } from "lucide-react";

import { runAi } from "../../features/api";
import { subscribeWorkflowExecutions, type WorkflowExecution } from "../../features/firestore";
import { useAuth } from "../../auth/AuthProvider";
import { agentByKey } from "../../design/agents";
import { AgentAvatar, ArtifactCard, PageHeader, ScorePill } from "../components/primitives";

function fmtDate(value: WorkflowExecution["updatedAt"]) {
  if (!value) return "";
  return value.toDate().toLocaleString("fr-FR");
}

export function AiConsolePage() {
  const { user } = useAuth();
  const [prompt, setPrompt] = useState("Crée un plan complet pour un site e-commerce camerounais : conception, frontend, backend, déploiement.");
  const [history, setHistory] = useState<WorkflowExecution[]>([]);
  const exec = useMutation({ mutationFn: (input: string) => runAi(input, "default-project") });

  useEffect(() => {
    if (!user) return undefined;
    return subscribeWorkflowExecutions(user.uid, (items) => setHistory(items), () => {});
  }, [user]);

  const data = exec.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Orchestration"
        title="Console workflow multi-agents"
        subtitle="Décrivez un projet. Le planificateur le découpe en sous-tâches et orchestre les bons spécialistes, jusqu'à la revue finale."
      />

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
        <section className="space-y-5">
          <div className="card p-5">
            <label className="label">Brief du projet</label>
            <textarea
              className="field mt-2 h-32 resize-none"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Décrivez votre projet ou la tâche à réaliser…"
            />
            <div className="mt-3 flex items-center justify-between">
              <span className="text-xs text-faint">Astuce : plus le brief est précis, meilleurs sont les livrables.</span>
              <button onClick={() => exec.mutate(prompt)} disabled={exec.isPending || !prompt.trim()} className="btn-primary">
                <Play size={15} />{exec.isPending ? "Exécution…" : "Lancer le workflow"}
              </button>
            </div>
          </div>

          {exec.isError && (
            <div className="card border-danger/25 bg-danger/[0.04] p-4 text-sm text-danger">
              Erreur d'exécution. Vérifiez que le serveur (port 3001) et le service IA (port 8000) sont démarrés.
            </div>
          )}

          {exec.isPending && (
            <div className="card p-6">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium text-muted">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
                Les agents travaillent…
              </div>
              <div className="space-y-2">
                {[0, 1, 2].map((i) => <div key={i} className="skeleton h-16" />)}
              </div>
            </div>
          )}

          {data && (
            <div className="space-y-5">
              {/* Plan */}
              <div className="card p-5">
                <div className="mb-3 flex items-center gap-2"><FileStack size={16} className="text-brand-600" /><h3 className="font-display text-sm font-semibold text-ink">Plan d'exécution</h3></div>
                <ol className="space-y-2">
                  {data.plan.map((p, i) => (
                    <li key={p.id} className="flex items-center gap-3 rounded-xl border border-line bg-surface-2/40 px-3 py-2">
                      <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-surface text-[11px] font-bold text-muted ring-1 ring-line">{i + 1}</span>
                      <AgentAvatar agentKey={p.assigned_agent} size="sm" />
                      <span className="min-w-0 flex-1 truncate text-sm text-ink-soft">{p.title}</span>
                      <span className="hidden text-xs text-faint sm:block">{agentByKey(p.assigned_agent)?.role ?? p.assigned_agent}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {/* Responses */}
              <div className="space-y-3">
                <h3 className="eyebrow">Livrables des agents</h3>
                {data.responses.map((r, idx) => {
                  const arts = Array.isArray(r.artifacts) ? (r.artifacts as Array<{ type?: string; title?: string; content?: string }>) : [];
                  return (
                    <div key={`${r.agent}-${idx}`} className="card p-4">
                      <div className="flex items-center gap-2.5">
                        <AgentAvatar agentKey={r.agent} size="sm" />
                        <span className="font-display text-sm font-semibold text-ink">{agentByKey(r.agent)?.role ?? r.agent}</span>
                        <span className="ml-auto"><ScorePill score={r.score} /></span>
                      </div>
                      <p className="mt-2.5 text-sm leading-relaxed text-ink-soft">{r.summary}</p>
                      {arts.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {arts.map((a, i) => <ArtifactCard key={i} index={i} type={a.type} title={a.title} content={a.content} />)}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Timeline */}
              <div className="card p-5">
                <div className="mb-3 flex items-center gap-2"><Clock size={16} className="text-brand-600" /><h3 className="font-display text-sm font-semibold text-ink">Déroulé</h3></div>
                <ul className="space-y-1.5">
                  {data.timeline.map((t, idx) => (
                    <li key={`${t.node}-${idx}`} className="flex items-center gap-2 text-sm">
                      {t.success === false ? <XCircle size={15} className="text-danger" /> : <CheckCircle2 size={15} className="text-brand-600" />}
                      <span className="text-ink-soft">{agentByKey(t.node)?.role ?? t.node}</span>
                      {t.ended_at && <span className="ml-auto text-xs text-faint">{new Date(t.ended_at).toLocaleTimeString("fr-FR")}</span>}
                    </li>
                  ))}
                </ul>
                <div className="mt-3 border-t border-line pt-3 text-xs text-faint">Workflow <span className="font-mono text-muted">{data.workflow_id}</span></div>
              </div>
            </div>
          )}
        </section>

        {/* History */}
        <aside className="card flex h-fit flex-col p-5 lg:sticky lg:top-24">
          <div className="mb-3 flex items-center gap-2"><History size={16} className="text-brand-600" /><h3 className="font-display text-sm font-semibold text-ink">Historique</h3></div>
          {history.length === 0 ? (
            <p className="py-6 text-center text-sm text-faint">Aucune exécution enregistrée pour l'instant.</p>
          ) : (
            <div className="space-y-2">
              {history.map((item) => {
                const tone = item.status === "succeeded" ? "text-brand-700 bg-brand-600/10" : item.status === "failed" ? "text-danger bg-danger/8" : "text-clay-700 bg-clay-500/12";
                return (
                  <article key={item.workflowId} className="rounded-xl border border-line bg-surface-2/40 p-3">
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <span className={`badge border-transparent ${tone}`}>{item.status}</span>
                      <span className="text-[11px] text-faint">{fmtDate(item.updatedAt)}</span>
                    </div>
                    <p className="line-clamp-2 text-xs text-ink-soft">{item.input}</p>
                  </article>
                );
              })}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
