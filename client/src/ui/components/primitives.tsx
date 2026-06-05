import { useState, type ReactNode } from "react";
import { Check, Copy, Download, type LucideIcon } from "lucide-react";
import { agentByKey } from "../../design/agents";
import { POLE_STYLE, type Pole } from "../../design/tokens";

/* ── Agent avatar (icon in a tinted, ringed square) ──────────────────────── */
export function AgentAvatar({
  agentKey, size = "md", className = "",
}: { agentKey: string; size?: "sm" | "md" | "lg"; className?: string }) {
  const agent = agentByKey(agentKey);
  const Icon = agent?.Icon;
  const style = agent ? POLE_STYLE[agent.pole] : POLE_STYLE.Veille;
  const dims = size === "lg" ? "h-12 w-12 rounded-2xl" : size === "sm" ? "h-7 w-7 rounded-lg" : "h-9 w-9 rounded-xl";
  const ic = size === "lg" ? 22 : size === "sm" ? 15 : 18;
  return (
    <span className={`inline-flex shrink-0 items-center justify-center ring-1 ${dims} ${style.ring} ${className}`}>
      {Icon ? <Icon size={ic} strokeWidth={1.9} /> : null}
    </span>
  );
}

/* ── Pole chip ───────────────────────────────────────────────────────────── */
export function PoleChip({ pole }: { pole: Pole }) {
  return <span className={`badge ${POLE_STYLE[pole].chip}`}><span className={`h-1.5 w-1.5 rounded-full ${POLE_STYLE[pole].dot}`} />{pole}</span>;
}

/* ── Page header ─────────────────────────────────────────────────────────── */
export function PageHeader({
  eyebrow, title, subtitle, actions,
}: { eyebrow?: string; title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && <div className="eyebrow mb-1.5">{eyebrow}</div>}
        <h1 className="text-2xl font-bold text-ink sm:text-[1.7rem]">{title}</h1>
        {subtitle && <p className="mt-1 max-w-xl text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}

/* ── Stat card ───────────────────────────────────────────────────────────── */
export function StatCard({
  icon: Icon, label, value, hint, accent = "text-brand-600",
}: { icon: LucideIcon; label: string; value: ReactNode; hint?: string; accent?: string }) {
  return (
    <div className="card group p-5 transition-shadow hover:shadow-lift">
      <div className="flex items-center justify-between">
        <span className="eyebrow">{label}</span>
        <Icon size={18} strokeWidth={1.9} className={`${accent} opacity-70`} />
      </div>
      <div className="mt-3 font-display text-3xl font-bold tabular-nums text-ink">{value}</div>
      {hint && <div className="mt-1 text-xs text-faint">{hint}</div>}
    </div>
  );
}

/* ── Empty state ─────────────────────────────────────────────────────────── */
export function EmptyState({
  icon: Icon, title, hint, action,
}: { icon: LucideIcon; title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="card flex flex-col items-center justify-center px-8 py-14 text-center">
      <span className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-2 text-faint ring-1 ring-line">
        <Icon size={24} strokeWidth={1.7} />
      </span>
      <div className="font-display text-base font-semibold text-ink-soft">{title}</div>
      {hint && <div className="mt-1 max-w-xs text-sm text-muted">{hint}</div>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

/* ── Score meter ─────────────────────────────────────────────────────────── */
export function ScorePill({ score }: { score: number }) {
  const pct = Math.round(Math.max(0, Math.min(1, score)) * 100);
  const tone = pct >= 80 ? "text-brand-700 bg-brand-600/10" : pct >= 60 ? "text-clay-700 bg-clay-500/12" : "text-danger bg-danger/8";
  return <span className={`badge border-transparent ${tone}`}>Qualité {pct}%</span>;
}

/* ── Copy + download for artifacts/deliverables ──────────────────────────── */
export function CopyButton({ text, label = "Copier" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      onClick={() => { void navigator.clipboard?.writeText(text).then(() => { setDone(true); setTimeout(() => setDone(false), 1600); }); }}
      className="btn-ghost btn-sm"
      type="button"
    >
      {done ? <Check size={14} className="text-brand-600" /> : <Copy size={14} />}
      {done ? "Copié" : label}
    </button>
  );
}

export function DownloadButton({ text, filename }: { text: string; filename: string }) {
  const onClick = () => {
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };
  return <button onClick={onClick} className="btn-ghost btn-sm" type="button"><Download size={14} />Exporter</button>;
}

/* ── Deliverable / artifact card with copy + export ──────────────────────── */
export function ArtifactCard({
  index, type, title, content,
}: { index: number; type?: string; title?: string; content?: string }) {
  const safeTitle = title || `Livrable ${index + 1}`;
  const body = content ?? "";
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface-2/40">
      <div className="flex items-center gap-2 border-b border-line px-4 py-2.5">
        {type && <span className="badge border-line-strong bg-surface text-muted">{type}</span>}
        <span className="truncate text-sm font-semibold text-ink-soft">{safeTitle}</span>
        <div className="ml-auto flex items-center gap-1">
          <CopyButton text={body} />
          <DownloadButton text={body} filename={`${safeTitle.replace(/[^\w\-]+/g, "_").slice(0, 40)}.md`} />
        </div>
      </div>
      <pre className="max-h-96 overflow-auto whitespace-pre-wrap px-4 py-3 font-mono text-[12.5px] leading-relaxed text-ink-soft">{body}</pre>
    </div>
  );
}

/* ── Skeleton block ──────────────────────────────────────────────────────── */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}
