import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { isFirebaseEnabled } from "../lib/firebase";
import { useAuth } from "./AuthProvider";
import { LoginPage } from "../ui/pages/LoginPage";
import { RegisterPage } from "../ui/pages/RegisterPage";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { loading, user } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [slowLoad, setSlowLoad] = useState(false);

  useEffect(() => {
    if (!loading) return;
    const t = setTimeout(() => setSlowLoad(true), 2500);
    return () => clearTimeout(t);
  }, [loading]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-paper text-ink">
        <div className="max-w-sm space-y-3 rounded-2xl border border-line bg-surface px-6 py-5 text-center text-sm shadow-card">
          <div className="flex items-center justify-center gap-2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
            <span className="text-muted">Connexion…</span>
          </div>
          {slowLoad && (
            <p className="text-xs leading-relaxed text-faint">
              Connexion lente. Vérifiez que les variables
              <span className="text-brand-700"> VITE_FIREBASE_*</span> sont définies
              et que votre domaine est autorisé dans la console Firebase.
            </p>
          )}
        </div>
      </main>
    );
  }

  // No Firebase configured — bypass auth, show app directly
  if (!isFirebaseEnabled) {
    return children;
  }

  if (!user) {
    return mode === "login" ? (
      <LoginPage onSwitchToRegister={() => setMode("register")} />
    ) : (
      <RegisterPage onSwitchToLogin={() => setMode("login")} />
    );
  }

  return children;
}
