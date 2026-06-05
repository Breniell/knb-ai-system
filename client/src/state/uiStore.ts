import { create } from "zustand";

export type PageKey =
  | "dashboard"
  | "agents"
  | "console"
  | "formation"
  | "projects"
  | "tasks"
  | "memory"
  | "monitoring"
  | "analytics"
  | "settings";

type UiState = {
  page: PageKey;
  setPage: (page: PageKey) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
};

export const useUiStore = create<UiState>((set) => ({
  page: "dashboard",
  setPage: (page) => set({ page, sidebarOpen: false }),
  sidebarOpen: false,
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
}));
