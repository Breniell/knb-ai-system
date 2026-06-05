import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Plus, ListChecks, X } from "lucide-react";

import { createTask, getProjects, getTasks } from "../../features/api";
import type { Task } from "../../types";
import { EmptyState, PageHeader, Skeleton } from "../components/primitives";

const STATUS: Record<Task["status"], { label: string; cls: string }> = {
  TODO: { label: "À faire", cls: "border-line-strong bg-surface-2 text-muted" },
  IN_PROGRESS: { label: "En cours", cls: "border-info/25 bg-info/[0.08] text-info" },
  DONE: { label: "Terminé", cls: "border-brand-600/25 bg-brand-600/[0.08] text-brand-700" },
  BLOCKED: { label: "Bloqué", cls: "border-danger/25 bg-danger/[0.06] text-danger" },
};

export function TasksPage() {
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [showForm, setShowForm] = useState(false);

  const projects = useQuery({ queryKey: ["projects"], queryFn: async () => (await getProjects()).projects });
  const tasks = useQuery({ queryKey: ["tasks", filterProject], queryFn: async () => (await getTasks(filterProject || undefined)).tasks });
  const create = useMutation({
    mutationFn: () => createTask({ projectId, title: title.trim(), description: description.trim() || undefined }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["tasks"] }); setTitle(""); setDescription(""); setProjectId(""); setShowForm(false); },
  });

  const allProjects = projects.data ?? [];
  const allTasks = tasks.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Travail"
        title="Tâches"
        subtitle={tasks.isLoading ? "Chargement…" : `${allTasks.length} tâche${allTasks.length !== 1 ? "s" : ""}`}
        actions={
          <>
            <select value={filterProject} onChange={(e) => setFilterProject(e.target.value)} className="field max-w-[180px] py-2">
              <option value="">Tous les projets</option>
              {allProjects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <button onClick={() => setShowForm((v) => !v)} className="btn-primary">{showForm ? <X size={15} /> : <Plus size={15} />}{showForm ? "Fermer" : "Nouvelle tâche"}</button>
          </>
        }
      />

      {showForm && (
        <section className="card animate-scale-in space-y-3 p-5">
          <h3 className="font-display text-sm font-semibold text-ink">Nouvelle tâche</h3>
          <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="field">
            <option value="">Sélectionner un projet</option>
            {allProjects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Titre de la tâche" className="field" />
          <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description (optionnelle)" className="field" />
          {create.isError && <div className="rounded-lg border border-danger/25 bg-danger/[0.05] px-3 py-2 text-sm text-danger">Erreur lors de la création.</div>}
          <div className="flex gap-2">
            <button onClick={() => projectId && title.trim() && create.mutate()} disabled={!projectId || !title.trim() || create.isPending} className="btn-primary">{create.isPending ? "Création…" : "Créer"}</button>
            <button onClick={() => { setShowForm(false); setTitle(""); setDescription(""); setProjectId(""); }} className="btn-ghost">Annuler</button>
          </div>
        </section>
      )}

      {tasks.isError && <div className="card border-danger/25 bg-danger/[0.04] p-5 text-sm text-danger">Impossible de charger les tâches.</div>}

      {tasks.isLoading ? (
        <div className="space-y-2">{[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : allTasks.length === 0 ? (
        <EmptyState icon={ListChecks} title="Aucune tâche" hint={filterProject ? "Aucune tâche pour ce projet." : "Créez votre première tâche."} />
      ) : (
        <div className="space-y-2">
          {allTasks.map((t) => {
            const sc = STATUS[t.status];
            const project = allProjects.find((p) => p.id === t.projectId);
            return (
              <article key={t.id} className="card flex items-start gap-3 px-4 py-3 transition-colors hover:border-line-strong">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-ink">{t.title}</span>
                    <span className={`badge ${sc.cls}`}>{sc.label}</span>
                  </div>
                  {t.description && <div className="mt-1 line-clamp-1 text-xs text-muted">{t.description}</div>}
                  <div className="mt-1.5 flex items-center gap-3 text-xs text-faint">
                    {project && <span className="text-muted">{project.name}</span>}
                    <span>{new Date(t.createdAt).toLocaleDateString("fr-FR")}</span>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
