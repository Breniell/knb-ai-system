import { initializeApp, type FirebaseApp } from "firebase/app";
import { connectAuthEmulator, getAuth, type Auth } from "firebase/auth";
import { type Firestore } from "firebase/firestore";

import { env } from "../config/env";

const isFirebaseEnabled = Boolean(env.firebase.apiKey);

let firebaseApp: FirebaseApp | null = null;
let auth: Auth | null = null;
let db: Firestore | null = null;

if (isFirebaseEnabled) {
  try {
    firebaseApp = initializeApp({
      apiKey: env.firebase.apiKey,
      authDomain: env.firebase.authDomain,
      projectId: env.firebase.projectId,
      storageBucket: env.firebase.storageBucket,
    });
    auth = getAuth(firebaseApp);

    if (env.firebase.authEmulatorUrl && auth) {
      connectAuthEmulator(auth, env.firebase.authEmulatorUrl, { disableWarnings: true });
    }
  } catch (err) {
    console.error("[KNB] Firebase init failed:", err);
  }
} else {
  console.warn("[KNB] VITE_FIREBASE_API_KEY not set — no-auth mode.");
}

/**
 * Call once at app startup (e.g. main.tsx) to lazily initialise Firestore.
 * Deferring the import() keeps _CacheManager (which calls window.requestIdleCallback)
 * out of the module-evaluation critical path, fixing the Firebase v12
 * "window is not defined" ReferenceError in Vite ESM builds.
 */
export async function initFirestore(): Promise<void> {
  if (!firebaseApp || db) return;
  try {
    const {
      initializeFirestore,
      memoryLocalCache,
      connectFirestoreEmulator,
    } = await import("firebase/firestore");

    db = initializeFirestore(firebaseApp, { localCache: memoryLocalCache() });

    if (env.firebase.firestoreEmulatorHost && db) {
      const [host, port] = env.firebase.firestoreEmulatorHost.split(":");
      if (host && port) connectFirestoreEmulator(db, host, Number(port));
    }
  } catch (err) {
    console.error("[KNB] Firestore lazy init failed:", err);
  }
}

export { firebaseApp, auth, db, isFirebaseEnabled };
