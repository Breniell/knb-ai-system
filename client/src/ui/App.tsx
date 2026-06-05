import { useEffect, useMemo, useState } from "react";
import { Menu, X, LogOut, Wifi, WifiOff, Circle } from "lucide-react";

import { apiFetch } from "../lib/http";
import { getSocket } from "../lib/socket";
import { useAuth } from "../auth/AuthProvider";
import { useUiStore, type PageKey } from "../state/uiStore";
import { Sidebar } from "./components/Sidebar";

import { DashboardPage } from "./pages/DashboardPage";
import { KnbAgentsPage } from "./pages/KnbAgentsPage";
import { AiConsolePage } from "./pages/AiConsolePage";
import { FormationPage } from "./pages/FormationPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { TasksPage } from "./pages/TasksPage";
import { MemoryPage } from "./pages/MemoryPage";
import { MonitoringPage } from "./pages/MonitoringPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { SettingsPage } from "./pages/SettingsPage";

type HealthResponse = { ok: true; service: "server"; time: string; requestId: string };

const PAGES: Record<PageKey, () => JSX.Element> = {
  dashboard: DashboardPage,
  agents: KnbAgentsPage,
  console: AiConsolePage,
  formation: FormationPage,
  projects: ProjectsPage,
  tasks: TasksPage,
  memory: MemoryPage,
  monitoring: MonitoringPage,
  analytics: AnalyticsPage,
  settings: SettingsPage,
};

function BrandMark() {
  return (
    <div className="flex items-center gap-2.5">
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-600 font-display text-lg font-bold text-white shadow-card">K</span>
      <div className="leading-none">
        <div className="font-display text-[15px] font-bold tracking-tight text-ink">KNB AI</div>
        <div className="mt-0.5 text-[11px] text-faint">Agence augmentée</div>
      </div>
    </div>
  );
}

export function App() {
  const { logout, user } = useAuth();
  const { page, setPage, sidebarOpen, setSidebarOpen } = useUiStore();
  const [apiHealth, setApiHealth] = useState<HealthResponse | null>(null);
  const [wsStatus, setWsStatus] = useState<"connected" | "disconnected">("disconnected");
  const socket = useMemo(() => getSocket(), []);

  useEffect(() => {
    let alive = true;
    const ping = () => apiFetch<HealthResponse>("/api/health").then((h) => { if (alive) setApiHealth(h); }).catch(() => { if (alive) setApiHealth(null); });
    void ping();
    const t = setInterval(ping, 15000);
    return () => { alive = false; clearInterval(t); };
  }, [user]);

  useEffect(() => {
    const onConnect = () => setWsStatus("connected");
    const onDisconnect = () => setWsStatus("disconnected");
    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    return () => { socket.off("connect", onConnect); socket.off("disconnect", onDisconnect); };
  }, [socket]);

  const Page = PAGES[page] ?? DashboardPage;

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[270px_1fr]">
      <aside className="sticky top-0 hidden h-screen flex-col border-r border-line bg-surface/70 backdrop-blur lg:flex">
        <div className="flex h-16 items-center border-b border-line px-5"><BrandMark /></div>
        <div className="flex-1 overflow-y-auto"><Sidebar page={page} onSelect={setPage} /></div>
        <div className="border-t border-line p-3">
          <div className="flex items-center gap-2.5 rounded-xl px-3 py-2">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-brand-600/10 text-xs font-bold text-brand-700">
              {(user?.email ?? "K").charAt(0).toUpperCase()}
            </span>
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-semibold text-ink-soft">{user?.displayName ?? user?.email ?? "Espace KNB"}</div>
              <div className="truncate text-[11px] text-faint">{user?.email ?? "mode local"}</div>
            </div>
            <button onClick={() => void logout()} className="rounded-lg p-1.5 text-faint hover:bg-surface-2 hover:text-danger" title="Déconnexion"><LogOut size={15} /></button>
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-ink/30 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <div className="absolute left-0 top-0 flex h-full w-72 flex-col bg-surface shadow-pop animate-fade-in">
            <div className="flex h-16 items-center justify-between border-b border-line px-5">
              <BrandMark />
              <button onClick={() => setSidebarOpen(false)} className="rounded-lg p-1.5 text-muted hover:bg-surface-2"><X size={18} /></button>
            </div>
            <div className="flex-1 overflow-y-auto"><Sidebar page={page} onSelect={setPage} /></div>
          </div>
        </div>
      )}

      <div className="flex min-h-screen min-w-0 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-line bg-paper/85 px-4 backdrop-blur sm:px-6">
          <button onClick={() => setSidebarOpen(true)} className="rounded-lg p-2 text-ink-soft hover:bg-surface-2 lg:hidden"><Menu size={18} /></button>
          <div className="lg:hidden"><BrandMark /></div>
          <div className="ml-auto flex items-center gap-2 text-xs">
            <span className={`badge ${apiHealth ? "border-brand-600/20 bg-brand-600/[0.08] text-brand-700" : "border-clay-500/25 bg-clay-500/10 text-clay-700"}`}>
              <Circle size={7} className={apiHealth ? "fill-brand-500 text-brand-500" : "fill-clay-500 text-clay-500"} />
              API {apiHealth ? "en ligne" : "hors ligne"}
            </span>
            <span className="badge border-line bg-surface text-muted">
              {wsStatus === "connected" ? <Wifi size={12} className="text-brand-600" /> : <WifiOff size={12} className="text-faint" />}
              Temps réel
            </span>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 sm:py-8">
          <div key={page} className="animate-fade-in"><Page /></div>
        </main>
      </div>
    </div>
  );
}
