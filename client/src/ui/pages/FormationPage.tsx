import { useCallback, useEffect, useRef, useState } from "react";
import { GraduationCap, RefreshCw, Zap, CheckCircle2, XCircle, BookOpen, Layers } from "lucide-react";

import { type AgentTrainingStatus, getTrainingStatus, learnCustomTopic, triggerAgentTraining } from "../../features/api";
import { AGENTS, agentByKey } from "../../design/agents";
import { POLE_STYLE } from "../../design/tokens";
import { AgentAvatar, PageHeader, PoleChip, StatCard, Skeleton } from "../components/primitives";

function formatRelative(iso: string | null): string {
  if (!iso) return "jamais";
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "à l'instant";
  if (m < 60) return `il y a ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `il y a ${h} h`;
  return `il y a ${Math.floor(h / 24)} j`;
}

function Bar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  const color = pct === 100 ? "bg-brand-500" : pct >= 60 ? "bg-brand-400" : pct > 0 ? "bg-clay-500" : "bg-line-strong";
  return <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-3"><div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} /></div>;
}

function parseTopics(raw: string): string[] {
  const lines = raw.split(/\n/).map((l) => l.trim()).filter(Boolean);
  const topics: string[] = [];
  for (const line of lines) {
    const urls = line.match(/https?:\/\/\S+/g);
    if (urls && urls.length > 1) topics.push(...urls);
    else topics.push(line);
  }
  return topics;
}

export function FormationPage() {
  const [statuses, setStatuses] = useState<AgentTrainingStatus[]>([]);
  const [summary, setSummary] = useState({ total_agents: 0, trained_agents: 0, total_topics_learned: 0 });
  const [loading, setLoading] = useState(true);
  const [trainingAll, setTrainingAll] = useState(false);
  const [trainingAgent, setTrainingAgent] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [customTopic, setCustomTopic] = useState("");
  const [customAgentId, setCustomAgentId] = useState("DevFrontendAgent");
  const [learnLoading, setLearnLoading] = useState(false);
  const [batchProgress, setBatchProgress] = useState<{ current: number; total: number; label: string } | null>(null);
  const [batchResults, setBatchResults] = useState<{ topic: string; insights: number; ok: boolean }[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(null), 4000); };

  const refresh = useCallback(async () => {
    try {
      const data = await getTrainingStatus();
      if (data.ok) { setStatuses(data.agents ?? []); setSummary(data.summary ?? summary); }
    } catch { /* silent */ } finally { setLoading(false); }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    void refresh();
    pollRef.current = setInterval(() => void refresh(), 20000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [refresh]);

  const trainAll = async () => {
    setTrainingAll(true);
    try { await triggerAgentTraining(undefined, false); showToast("Formation globale lancée — actualisation dans 20 s"); setTimeout(() => void refresh(), 3000); }
    catch { showToast("Erreur lors du lancement"); } finally { setTrainingAll(false); }
  };

  const trainOne = async (agentName: string) => {
    setTrainingAgent(agentName);
    try { await triggerAgentTraining(agentName, false); showToast(`Formation de ${agentByKey(agentName)?.role ?? agentName} lancée`); setTimeout(() => void refresh(), 3000); }
    catch { showToast("Erreur de formation"); } finally { setTrainingAgent(null); }
  };

  const learnCustom = async () => {
    const topics = parseTopics(customTopic);
    if (topics.length === 0) return;
    setLearnLoading(true); setBatchResults([]);
    let total = 0;
    for (let i = 0; i < topics.length; i++) {
      const topic = topics[i]!;
      setBatchProgress({ current: i + 1, total: topics.length, label: topic.length > 50 ? topic.slice(0, 47) + "…" : topic });
      try {
        const data = await learnCustomTopic(customAgentId, topic);
        setBatchResults((prev) => [...prev, { topic, insights: data.insights_count ?? 0, ok: data.ok }]);
        if (data.ok) total += data.insights_count ?? 0;
      } catch { setBatchResults((prev) => [...prev, { topic, insights: 0, ok: false }]); }
    }
    setBatchProgress(null); setLearnLoading(false);
    showToast(`${agentByKey(customAgentId)?.role} — ${topics.length} sujet(s), ${total} insights appris`);
    setCustomTopic(""); void refresh();
  };

  const globalPct = summary.total_agents > 0 ? Math.round((summary.trained_agents / summary.total_agents) * 100) : 0;

  return (
    <div className="space-y-7 pb-10">
      {toast && (
        <div className="fixed right-4 top-20 z-50 max-w-sm animate-fade-in rounded-xl border border-brand-600/25 bg-surface px-4 py-3 text-sm text-ink-soft shadow-pop">{toast}</div>
      )}

      <PageHeader
        eyebrow="Académie"
        title="Formation des agents"
        subtitle="Assignez des cours et des sources web. Vos agents s'auto-forment en continu et mémorisent ce qu'ils apprennent."
        actions={
          <>
            <button onClick={() => void refresh()} className="btn-outline"><RefreshCw size={15} />Actualiser</button>
            <button onClick={() => void trainAll()} disabled={trainingAll} className="btn-primary"><Zap size={15} />{trainingAll ? "Lancement…" : "Tout former"}</button>
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard icon={GraduationCap} label="Agents formés" value={`${summary.trained_agents}/${summary.total_agents}`} hint="objectif : tous opérationnels" />
        <StatCard icon={BookOpen} label="Sujets maîtrisés" value={summary.total_topics_learned} hint="connaissances acquises" accent="text-clay-500" />
        <StatCard icon={Layers} label="Progression" value={`${globalPct}%`} hint="couverture de l'équipe" accent="text-info" />
      </div>

      {/* Custom courses */}
      <section className="card p-6">
        <h2 className="font-display text-base font-semibold text-ink">Cours personnalisés</h2>
        <p className="mt-1 text-sm text-muted">Collez plusieurs URLs ou sujets, un par ligne. Chaque ligne est analysée puis mémorisée par l'agent choisi.</p>
        <textarea
          value={customTopic}
          onChange={(e) => setCustomTopic(e.target.value)}
          rows={5}
          placeholder={"https://react.dev/learn\nhttps://nextjs.org/docs/app\nAccessibilité WCAG bonnes pratiques\nhttps://www.prisma.io/docs"}
          className="field mt-4 resize-y font-mono text-[12.5px] leading-relaxed"
        />
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
          <select value={customAgentId} onChange={(e) => setCustomAgentId(e.target.value)} disabled={learnLoading} className="field max-w-xs">
            {AGENTS.map((a) => <option key={a.name} value={a.name}>{a.role}</option>)}
          </select>
          {customTopic.trim() && !learnLoading && <span className="text-xs text-faint">{parseTopics(customTopic).length} sujet(s) détecté(s)</span>}
          {batchProgress && (
            <span className="flex items-center gap-2 text-xs text-brand-700">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
              {batchProgress.current}/{batchProgress.total} — {batchProgress.label}
            </span>
          )}
          <button onClick={() => void learnCustom()} disabled={learnLoading || !customTopic.trim()} className="btn-ink sm:ml-auto">
            {learnLoading ? (batchProgress ? `${batchProgress.current}/${batchProgress.total}…` : "Apprentissage…") : "Assigner & former"}
          </button>
        </div>

        {batchResults.length > 0 && (
          <div className="card-quiet mt-4 space-y-1.5 p-4">
            <div className="eyebrow mb-1">Résultats — {agentByKey(customAgentId)?.role}</div>
            {batchResults.map((r, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                {r.ok ? <CheckCircle2 size={13} className="text-brand-600" /> : <XCircle size={13} className="text-danger" />}
                <span className="flex-1 truncate text-ink-soft">{r.topic.length > 60 ? r.topic.slice(0, 57) + "…" : r.topic}</span>
                {r.ok && <span className="text-faint">{r.insights} insight{r.insights !== 1 ? "s" : ""}</span>}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Agent grid */}
      <div>
        <div className="eyebrow mb-3">Agents & curriculums</div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-44" />)
            : AGENTS.map((agent) => {
                const status = statuses.find((s) => s.agent === agent.name);
                const learned = status?.topics_learned ?? 0;
                const total = status?.curriculum_size ?? agent.curriculum.length;
                const pct = status?.completion_pct ?? 0;
                const trained = status?.is_trained ?? false;
                const isExpanded = expanded === agent.name;
                return (
                  <div key={agent.name} className="card flex flex-col gap-3 p-4 transition-shadow hover:shadow-lift">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <AgentAvatar agentKey={agent.id} />
                        <div>
                          <div className="text-sm font-semibold leading-tight text-ink">{agent.role}</div>
                          <div className="mt-1"><PoleChip pole={agent.pole} /></div>
                        </div>
                      </div>
                      <span className={`badge ${trained ? "border-brand-600/25 bg-brand-600/[0.08] text-brand-700" : "border-line bg-surface-2 text-faint"}`}>
                        {trained ? "Formé" : "À former"}
                      </span>
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between text-xs text-muted"><span>{learned} / {total} sujets</span><span className="font-medium">{pct}%</span></div>
                      <Bar value={learned} max={total} />
                    </div>
                    <div className="text-xs text-faint">Dernière formation : {formatRelative(status?.last_trained ?? null)}</div>
                    <div className="mt-auto flex gap-2">
                      <button onClick={() => setExpanded(isExpanded ? null : agent.name)} className="btn-outline btn-sm flex-1">{isExpanded ? "Masquer" : "Programme"}</button>
                      <button onClick={() => void trainOne(agent.name)} disabled={trainingAgent === agent.name} className="btn-primary btn-sm flex-1">{trainingAgent === agent.name ? "…" : "Former"}</button>
                    </div>
                    {isExpanded && (
                      <div className="border-t border-line pt-3">
                        <div className="eyebrow mb-2">Programme</div>
                        <ul className="space-y-1.5">
                          {agent.curriculum.map((t, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-muted">
                              <span className={`mt-1 h-1 w-1 rounded-full ${POLE_STYLE[agent.pole].dot}`} /><span>{t}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                );
              })}
        </div>
      </div>
    </div>
  );
}
