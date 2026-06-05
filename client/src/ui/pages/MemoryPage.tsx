import { useState } from "react";
import { Search, Brain, SearchX } from "lucide-react";

import { searchMemory } from "../../features/api";
import type { MemorySearchResult } from "../../types";
import { EmptyState, PageHeader } from "../components/primitives";

export function MemoryPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MemorySearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    const q = query.trim();
    if (!q) return;
    setLoading(true); setError(null); setResults(null);
    try { const data = await searchMemory(q); setResults(data.results ?? []); }
    catch { setError("Erreur de connexion au service de mémoire."); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Connaissances" title="Mémoire IA" subtitle="Recherchez dans la base vectorielle des connaissances apprises et des livrables passés." />

      <section className="card p-4">
        <div className="flex items-center gap-2 rounded-xl border border-line bg-surface px-3 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-400/20">
          <Search size={17} className="text-faint" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void search()}
            placeholder="architecture microservices, authentification, Prisma…"
            className="flex-1 bg-transparent py-2.5 text-sm text-ink placeholder:text-faint focus:outline-none"
          />
          <button onClick={() => void search()} disabled={loading || !query.trim()} className="btn-primary btn-sm">{loading ? "Recherche…" : "Rechercher"}</button>
        </div>
      </section>

      {error && <div className="card border-danger/25 bg-danger/[0.04] p-5 text-sm text-danger">{error}</div>}

      {results !== null && (
        <div className="space-y-3">
          <div className="eyebrow">{results.length} résultat{results.length !== 1 ? "s" : ""} pour « {query} »</div>
          {results.length === 0 ? (
            <EmptyState icon={SearchX} title="Aucun résultat" hint="Essayez d'autres termes, ou alimentez la mémoire via la Formation." />
          ) : (
            results.map((r, idx) => (
              <article key={r.id ?? idx} className="card p-4 transition-colors hover:border-line-strong">
                <div className="mb-2 flex items-center justify-between gap-3">
                  {r.source && <span className="badge border-brand-600/20 bg-brand-600/[0.08] text-brand-700">{r.source}</span>}
                  {r.score !== undefined && <span className="text-xs text-faint">Pertinence <span className="font-semibold text-brand-700">{(r.score * 100).toFixed(0)}%</span></span>}
                </div>
                <p className="text-sm leading-relaxed text-ink-soft">{r.content}</p>
              </article>
            ))
          )}
        </div>
      )}

      {results === null && !loading && !error && (
        <EmptyState icon={Brain} title="Interrogez la mémoire" hint="Tapez un terme et lancez la recherche. La mémoire contient ce que vos agents ont appris." />
      )}
    </div>
  );
}
