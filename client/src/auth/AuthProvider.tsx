import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
  type User,
} from "firebase/auth";
import { doc, serverTimestamp, setDoc } from "firebase/firestore";

import { auth, db, isFirebaseEnabled } from "../lib/firebase";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function syncUserProfile(user: User) {
  if (!db) return;
  try {
    await setDoc(
      doc(db, "users", user.uid),
      { uid: user.uid, email: user.email, displayName: user.displayName, lastSeenAt: serverTimestamp() },
      { merge: true }
    );
  } catch {
    // Firestore profile sync should not prevent an authenticated session.
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isFirebaseEnabled || !auth) {
      // No Firebase configured — run in no-auth mode (all features accessible)
      setLoading(false);
      return;
    }

    // Safety timeout: if Firebase doesn't respond in 6 seconds, unblock the UI.
    // This handles cases where the Firebase project is misconfigured or the
    // Vercel domain is not yet whitelisted in Firebase Auth authorized domains.
    const timeout = setTimeout(() => {
      setLoading((prev) => {
        if (prev) {
          console.warn(
            "[KNB] Firebase Auth timed out after 6s — showing login page.\n" +
            "If you see this repeatedly, check:\n" +
            "  1. VITE_FIREBASE_* env vars are set in Vercel dashboard\n" +
            "  2. Your Vercel domain is added to Firebase Console → Authentication → Settings → Authorized domains"
          );
        }
        return false;
      });
    }, 6000);

    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      clearTimeout(timeout);
      if (firebaseUser) {
        await syncUserProfile(firebaseUser);
      }
      setUser(firebaseUser);
      setLoading(false);
    });

    return () => {
      clearTimeout(timeout);
      unsubscribe();
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      async login(email, password) {
        if (!auth) throw new Error("Firebase non configuré — vérifiez VITE_FIREBASE_API_KEY dans .env");
        await signInWithEmailAndPassword(auth, email, password);
      },
      async register(email, password, displayName) {
        if (!auth) throw new Error("Firebase non configuré — vérifiez VITE_FIREBASE_API_KEY dans .env");
        const credential = await createUserWithEmailAndPassword(auth, email, password);
        if (displayName) {
          await updateProfile(credential.user, { displayName });
        }
        if (db) {
          try {
            await setDoc(
              doc(db, "users", credential.user.uid),
              {
                uid: credential.user.uid,
                email: credential.user.email,
                displayName: displayName ?? credential.user.displayName,
                createdAt: serverTimestamp(),
                lastSeenAt: serverTimestamp(),
              },
              { merge: true }
            );
          } catch {
            // Auth account is source of truth; profile sync can retry on next session.
          }
        }
      },
      async logout() {
        if (!auth) return;
        await signOut(auth);
      },
    }),
    [loading, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
