export const env = {
  apiUrl: import.meta.env.VITE_API_URL ?? "http://localhost:3001",
  wsUrl: import.meta.env.VITE_WS_URL ?? "http://localhost:3001",
  firebase: {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY ?? "",
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN ?? "knb-ai-system.firebaseapp.com",
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID ?? "knb-ai-system",
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET ?? "knb-ai-system.firebasestorage.app",
    authEmulatorUrl: import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_URL,
    firestoreEmulatorHost: import.meta.env.VITE_FIRESTORE_EMULATOR_HOST,
  },
} as const;

