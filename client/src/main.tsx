import "./styles.css";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRoot } from "react-dom/client";

// Lazy Firestore init — deferred so Firebase v12's _CacheManager (which calls
// window.requestIdleCallback) never runs during module evaluation.
import { initFirestore } from "./lib/firebase";
void initFirestore();

import { AuthProvider } from "./auth/AuthProvider";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { App } from "./ui/App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <ProtectedRoute>
        <App />
      </ProtectedRoute>
    </AuthProvider>
  </QueryClientProvider>
);

