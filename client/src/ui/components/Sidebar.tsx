import {
  LayoutDashboard, MessagesSquare, Workflow, GraduationCap,
  FolderKanban, ListChecks, Brain, Activity, BarChart3, Settings,
  type LucideIcon,
} from "lucide-react";
import type { PageKey } from "../../state/uiStore";

type NavItem = { key: PageKey; label: string; Icon: LucideIcon };
type NavGroup = { heading: string; items: NavItem[] };

const GROUPS: NavGroup[] = [
  {
    heading: "Pilotage",
    items: [
      { key: "dashboard", label: "Tableau de bord", Icon: LayoutDashboard },
      { key: "agents", label: "Agents", Icon: MessagesSquare },
      { key: "console", label: "Console workflow", Icon: Workflow },
      { key: "formation", label: "Formation", Icon: GraduationCap },
    ],
  },
  {
    heading: "Travail",
    items: [
      { key: "projects", label: "Projets", Icon: FolderKanban },
      { key: "tasks", label: "Tâches", Icon: ListChecks },
      { key: "memory", label: "Mémoire", Icon: Brain },
    ],
  },
  {
    heading: "Système",
    items: [
      { key: "monitoring", label: "Monitoring", Icon: Activity },
      { key: "analytics", label: "Analytics", Icon: BarChart3 },
      { key: "settings", label: "Paramètres", Icon: Settings },
    ],
  },
];

export function Sidebar({ page, onSelect }: { page: PageKey; onSelect: (p: PageKey) => void }) {
  return (
    <nav className="flex h-full flex-col gap-6 px-3 py-5">
      {GROUPS.map((group) => (
        <div key={group.heading}>
          <div className="px-3 pb-1.5 text-[10.5px] font-semibold uppercase tracking-[0.16em] text-faint">
            {group.heading}
          </div>
          <div className="space-y-0.5">
            {group.items.map(({ key, label, Icon }) => {
              const active = page === key;
              return (
                <button
                  key={key}
                  onClick={() => onSelect(key)}
                  className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
                    active
                      ? "bg-brand-600/10 text-brand-800"
                      : "text-ink-soft hover:bg-surface-2 hover:text-ink"
                  }`}
                >
                  <Icon
                    size={18}
                    strokeWidth={active ? 2.1 : 1.8}
                    className={active ? "text-brand-600" : "text-faint group-hover:text-muted"}
                  />
                  <span>{label}</span>
                  {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-brand-500" />}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}
