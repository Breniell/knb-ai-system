# KNB AI System — Démarrage rapide (après corrections)

## Ce qui n'allait pas (et qui est corrigé)

Ton code n'était **pas cassé** : client, serveur et service IA compilent et les
35 tests passent. Le système paraissait mort à cause de **3 problèmes de
configuration/architecture**, maintenant corrigés :

1. **Décalage d'authentification (cause n°1 du « rien ne marche »).**
   Le client avait un « mode sans-auth » (qui te laissait entrer sans Firebase),
   mais le serveur, lui, **exigeait toujours un token Firebase** sur chaque route.
   Résultat : l'interface s'affichait, mais **chaque appel renvoyait 401**.
   → Corrigé : le serveur accepte maintenant un mode `DEV_NO_AUTH=true` qui injecte
   un utilisateur local. Le stack tourne désormais **sans aucune config Firebase**.

2. **Import dur de BeautifulSoup.** Si `beautifulsoup4` n'était pas installé,
   **tout le service IA refusait de démarrer**. → Corrigé : import optionnel.

3. **Deux fichiers `.env.example` contradictoires** (ports 8080 vs 3001, clé
   Firebase vide vs réelle). → Corrigé : un seul `.env.example` cohérent à la racine.

## Pourquoi « les agents n'arrivaient pas à se développer »

Sans clé LLM, chaque agent renvoie un **modèle figé avec des `[placeholders]`**.
Les agents ne deviennent intelligents (recherche → raisonnement → rédaction →
auto-critique → révision) **qu'avec une clé LLM**. C'est le seul ingrédient
manquant pour des livrables réels.

## Démarrer en 3 étapes

```bash
# 1. Créer le .env
cp .env.example .env

# 2. Mettre UNE clé LLM gratuite dans .env (Groq recommandé)
#    GROQ_API_KEY=gsk_...   →  https://console.groq.com/keys
#    (DEV_NO_AUTH=true est déjà réglé : pas besoin de Firebase)

# 3. Lancer
chmod +x start-dev.sh && ./start-dev.sh      # Linux/macOS/WSL
# ou  .\start-dev.ps1                          # Windows
```

Puis ouvrir :
- Interface : http://localhost:5173
- API serveur : http://localhost:8080/api/health
- Service IA : http://localhost:8000/healthz

## Pour aller plus loin (optionnel)

| Tu veux… | Ajoute dans `.env` |
|----------|--------------------|
| Mémoire sémantique (les agents se souviennent des projets) | `GEMINI_API_KEY` + `QDRANT_URL` |
| Recherche web pendant le raisonnement | `BRAVE_API_KEY` + `WEB_LEARNING_ENABLED=true` |
| Vraie authentification multi-utilisateurs | `DEV_NO_AUTH=false` + config Firebase complète |
| Historique persistant | PostgreSQL via `DATABASE_URL` (Docker `profile: full`) |

## Note de sécurité

L'ancien `ai-services/.env.example` contenait une vraie clé web Firebase et un
e-mail admin en clair. Les clés web Firebase ne sont pas vraiment secrètes (elles
finissent dans le bundle client), mais si ce dépôt est public, **régénère/limite
ce projet Firebase** et ne committe jamais de vrai compte de service.
