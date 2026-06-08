import { useEffect, useRef, useState } from "react";
import { Globe, Send, Trash2, Sparkles, CornerDownLeft } from "lucide-react";

import { chatWithAgent } from "../../features/api";
import { AGENTS, POLES, type AgentDef } from "../../design/agents";
import { POLE_STYLE } from "../../design/tokens";
import { AgentAvatar, ArtifactCard, ScorePill } from "../components/primitives";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  artifacts?: unknown[];
  followups?: string[];
  score?: number;
}

export function KnbAgentsPage() {
  const [activeAgent, setActiveAgent] = useState<AgentDef>(AGENTS[0]!);
  const [conversations, setConversations] = useState<Map<string, Message[]>>(new Map());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [webLearning, setWebLearning] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  const messages = conversations.get(activeAgent.id) ?? [];
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages.length, loading]);

  const push = (msg: Message) =>
    setConversations((prev) => {
      const next = new Map(prev);
      next.set(activeAgent.id, [...(prev.get(activeAgent.id) ?? []), msg]);
      return next;
    });

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    setInput("");
    setLoading(true);
    push({ id: `u-${Date.now()}`, role: "user", content: text });
    try {
      const history = (conversations.get(activeAgent.id) ?? []).map((m) => ({ role: m.role, content: m.content }));
      const result = await chatWithAgent(activeAgent.id, text, history, "knb-agents", webLearning);
      const resp = result.response;
      push({
        id: `a-${Date.now()}`, role: "assistant",
        content: resp?.summary ?? "Aucune réponse",
        artifacts: Array.isArray(resp?.artifacts) ? resp.artifacts : [],
        followups: resp?.followups ?? [],
        score: resp?.score,
      });
    } catch (err) {
      let msg = "Connexion impossible au serveur.";
      if (err instanceof Error) {
        try {
          const parsed = JSON.parse(err.message) as { error?: { message?: string } };
          msg = parsed?.error?.message ?? err.message;
        } catch {
          msg = err.message || msg;
        }
      }
      push({ id: `e-${Date.now()}`, role: "assistant", content: msg });
    } finally {
      setLoading(false);
    }
  };

  const clear = () => setConversations((prev) => { const n = new Map(prev); n.delete(activeAgent.id); return n; });

  return (
    <div className="grid h-[calc(100vh-9rem)] grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
      <aside className="card hidden flex-col overflow-hidden lg:flex">
        <div className="border-b border-line px-4 py-3">
          <div className="eyebrow">Équipe</div>
          <button
            onClick={() => setWebLearning((v) => !v)}
            className={`mt-2 flex w-full items-center gap-2 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors ${
              webLearning ? "border-brand-600/30 bg-brand-600/[0.08] text-brand-700" : "border-line bg-surface text-muted hover:text-ink"
            }`}
          >
            <Globe size={13} /> Veille web {webLearning ? "active" : "inactive"}
            <span className={`ml-auto h-3.5 w-6 rounded-full transition-colors ${webLearning ? "bg-brand-500" : "bg-line-strong"}`}>
              <span className={`block h-3 w-3 translate-y-[1px] rounded-full bg-white shadow transition-transform ${webLearning ? "translate-x-[11px]" : "translate-x-[2px]"}`} />
            </span>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 py-2">
          {POLES.map((pole) => (
            <div key={pole} className="mb-2">
              <div className="px-2 py-1 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-faint">{pole}</div>
              {AGENTS.filter((a) => a.pole === pole).map((agent) => {
                const count = (conversations.get(agent.id) ?? []).length;
                const active = agent.id === activeAgent.id;
                return (
                  <button
                    key={agent.id}
                    onClick={() => setActiveAgent(agent)}
                    className={`flex w-full items-center gap-2.5 rounded-xl px-2 py-1.5 text-left transition-colors ${active ? "bg-brand-600/10" : "hover:bg-surface-2"}`}
                  >
                    <AgentAvatar agentKey={agent.id} size="sm" />
                    <span className={`flex-1 truncate text-[13px] font-medium ${active ? "text-brand-800" : "text-ink-soft"}`}>{agent.role}</span>
                    {count > 0 && <span className="rounded-full bg-surface-2 px-1.5 text-[10px] font-semibold text-muted">{Math.ceil(count / 2)}</span>}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </aside>

      <section className="card flex min-w-0 flex-col overflow-hidden">
        <header className="flex items-center gap-3 border-b border-line px-5 py-3">
          <AgentAvatar agentKey={activeAgent.id} />
          <div className="min-w-0">
            <div className="truncate font-display text-sm font-semibold text-ink">{activeAgent.role}</div>
            <div className="truncate text-xs text-muted">{activeAgent.description}</div>
          </div>
          <select
            value={activeAgent.id}
            onChange={(e) => setActiveAgent(AGENTS.find((a) => a.id === e.target.value)!)}
            className="ml-auto field-quiet max-w-[42%] py-1.5 text-xs lg:hidden"
          >
            {AGENTS.map((a) => <option key={a.id} value={a.id}>{a.role}</option>)}
          </select>
          {messages.length > 0 && (
            <button onClick={clear} className="ml-auto hidden btn-ghost btn-sm lg:inline-flex"><Trash2 size={14} />Effacer</button>
          )}
        </header>

        <div className="flex-1 space-y-5 overflow-y-auto px-4 py-5 sm:px-6">
          {messages.length === 0 ? (
            <Welcome agent={activeAgent} onPick={(s) => void sendMessage(s)} />
          ) : (
            messages.map((m) => <Bubble key={m.id} m={m} agent={activeAgent} />)
          )}
          {loading && <Typing agent={activeAgent} />}
          <div ref={endRef} />
        </div>

        <div className="border-t border-line px-4 py-3 sm:px-5">
          <div className="flex items-end gap-2 rounded-2xl border border-line bg-surface p-2 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-400/20">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void sendMessage(input); } }}
              placeholder={`Écrire à ${activeAgent.role}…`}
              rows={1}
              className="max-h-40 flex-1 resize-none bg-transparent px-2.5 py-2 text-sm text-ink placeholder:text-faint focus:outline-none"
            />
            <button onClick={() => void sendMessage(input)} disabled={loading || !input.trim()} className="btn-primary px-3.5 py-2.5">
              <Send size={15} />
            </button>
          </div>
          <div className="mt-1.5 flex items-center gap-1 px-1 text-[11px] text-faint">
            <CornerDownLeft size={11} /> Entrée pour envoyer · Maj+Entrée pour une nouvelle ligne
          </div>
        </div>
      </section>
    </div>
  );
}

function Welcome({ agent, onPick }: { agent: AgentDef; onPick: (s: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center py-8 text-center">
      <AgentAvatar agentKey={agent.id} size="lg" />
      <h2 className="mt-4 font-display text-xl font-bold text-ink">{agent.role}</h2>
      <p className="mt-1 max-w-sm text-sm text-muted">{agent.description}</p>
      <div className="mt-7 grid w-full max-w-xl grid-cols-1 gap-2.5 sm:grid-cols-2">
        {agent.starters.map((s, i) => (
          <button
            key={i}
            onClick={() => onPick(s)}
            className="group flex items-start gap-2 rounded-xl border border-line bg-surface px-3.5 py-3 text-left text-sm text-ink-soft transition-all hover:border-brand-300 hover:bg-brand-50/40 hover:shadow-card"
          >
            <Sparkles size={14} className="mt-0.5 shrink-0 text-faint group-hover:text-brand-500" />
            <span>{s}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function Bubble({ m, agent }: { m: Message; agent: AgentDef }) {
  const isUser = m.role === "user";
  const artifacts = (m.artifacts as Array<{ type?: string; title?: string; content?: string }>) ?? [];
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-tr-md bg-ink px-4 py-2.5 text-sm leading-relaxed text-paper">
          <p className="whitespace-pre-wrap">{m.content}</p>
        </div>
      </div>
    );
  }
  return (
    <div className="flex gap-3">
      <AgentAvatar agentKey={agent.id} size="sm" className="mt-0.5" />
      <div className="min-w-0 flex-1 space-y-2.5">
        <div className="rounded-2xl rounded-tl-md border border-line bg-surface-2/40 px-4 py-3">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-soft">{m.content}</p>
          {m.score !== undefined && <div className="mt-2"><ScorePill score={m.score} /></div>}
        </div>
        {artifacts.length > 0 && (
          <div className="space-y-2">
            {artifacts.map((a, i) => <ArtifactCard key={i} index={i} type={a.type} title={a.title} content={a.content} />)}
          </div>
        )}
        {m.followups && m.followups.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {m.followups.map((f, i) => (
              <span key={i} className="rounded-full border border-line bg-surface px-2.5 py-1 text-xs text-muted">{f}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Typing({ agent }: { agent: AgentDef }) {
  const style = POLE_STYLE[agent.pole];
  return (
    <div className="flex items-center gap-3">
      <AgentAvatar agentKey={agent.id} size="sm" />
      <div className="flex items-center gap-1 rounded-2xl rounded-tl-md border border-line bg-surface-2/40 px-4 py-3">
        {[0, 1, 2].map((i) => (
          <span key={i} className={`h-1.5 w-1.5 animate-bounce rounded-full ${style.dot}`} style={{ animationDelay: `${i * 0.15}s` }} />
        ))}
      </div>
    </div>
  );
}
