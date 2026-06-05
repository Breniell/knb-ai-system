import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Plus, FolderKanban, X } from "lucide-react";

import { createProject, getProjects } from "../../features/api";
import { EmptyState, PageHeader, Skeleton } from "../components/primitives";

export function ProjectsPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [showForm, setShowForm] = useState(false);

  const projects = useQuery({ queryKey: ["projects"], queryFn: async () => (await getProjects()).projects });
  const create = useMutation({
    mutationFn: () => createProject(name.trim(), description.trim() || undefined),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["projects"] }); setName(""); setDescription(""); setShowForm(false); },
  });

  const data = projects.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Travail"
        title="Projets"
        subtitle={projects.isLoading ? "Chargement…" : `${data.length} dossier${data.length !== 1 ? "s" : ""} client`}
        actions={<button onClick={() => setShowForm((v) => !v)} className="btn-primary">{showForm ? <X size={15} /> : <Plus size={15} />}{showForm ? "Fermer" : "Nouveau projet"}</button>}
      />

      {showForm && (
        <section className="card animate-scale-in space-y-3 p-5">
          <h3 className="font-display text-sm font-semibold text-ink">Nouveau projet</h3>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom du projet" className="field" />
          <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description (optionnelle)" className="field" />
          {create.isError && <div className="rounded-lg border border-danger/25 bg-danger/[0.05] px-3 py-2 text-sm text-danger">Erreur lors de la création.</div>}
          <div className="flex gap-2">
            <button onClick={() => name.trim() && create.mutate()} disabled={!name.trim() || create.isPending} className="btn-primary">{create.isPending ? "Création…" : "Créer"}</button>
            <button onClick={() => { setShowForm(false); setName(""); setDescription(""); }} className="btn-ghost">Annuler</button>
          </div>
        </section>
      )}

      {projects.isError && <div className="card border-danger/25 bg-danger/[0.04] p-5 text-sm text-danger">Impossible de charger les projets.</div>}

      {projects.isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
      ) : data.length === 0 ? (
        <EmptyState icon={FolderKanban} title="Aucun projet pour l'instant" hint="Créez votre premier dossier client pour commencer."
          action={<button onClick={() => setShowForm(true)} className="btn-primary"><Plus size={15} />Nouveau projet</button>} />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((p) => (
            <article key={p.id} className="card flex items-start gap-3 p-4 transition-all hover:-translate-y-0.5 hover:shadow-lift">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-600/10 font-display text-base font-bold text-brand-700 ring-1 ring-brand-600/15">{p.name.charAt(0).toUpperCase()}</span>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold text-ink">{p.name}</div>
                {p.description && <div className="mt-0.5 line-clamp-2 text-xs text-muted">{p.description}</div>}
                <div className="mt-2 flex items-center gap-1.5 text-xs text-faint"><span className="h-1.5 w-1.5 rounded-full bg-brand-500" />{new Date(p.createdAt).toLocaleDateString("fr-FR")}</div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
