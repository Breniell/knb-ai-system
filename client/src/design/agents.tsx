import type { LucideIcon } from "lucide-react";
import {
  Briefcase, TrendingUp, Megaphone, Building2, LayoutTemplate, ServerCog,
  Smartphone, Rocket, FlaskConical, Palette, PencilRuler, PenLine,
  ClipboardList, LifeBuoy, Wallet, ShieldCheck, Bot,
} from "lucide-react";
import type { Pole } from "./tokens";

export interface AgentDef {
  id: string;        // API id (snake_case)
  name: string;      // class name returned by the engine (PascalCase)
  role: string;
  pole: Pole;
  description: string;
  Icon: LucideIcon;
  starters: string[];
  curriculum: string[];
}

export const AGENTS: AgentDef[] = [
  {
    id: "commercial_agent", name: "CommercialAgent", role: "Commercial & Ventes", pole: "Business", Icon: Briefcase,
    description: "Devis, propositions commerciales, objections, closing, CRM",
    starters: [
      "Génère un devis pour un site vitrine à 200 000 FCFA",
      "Rédige une proposition commerciale pour une PME de BTP",
      "Comment répondre à l'objection « c'est trop cher » ?",
      "Crée un script de prospection pour des boutiques",
    ],
    curriculum: ["Négociation BtoB BtoC techniques closing", "Tarification projets web mobile FCFA", "Proposition commerciale pitch deck", "CRM pipeline commercial gestion", "Paiement Mobile Money contrats"],
  },
  {
    id: "marketing_agent", name: "MarketingAgent", role: "Stratégie Marketing", pole: "Business", Icon: TrendingUp,
    description: "Marketing digital, SEO/SEM, campagnes, analytics, growth",
    starters: [
      "Plan marketing digital sur 3 mois, budget 300k FCFA",
      "Meilleurs canaux d'acquisition pour une agence web au Cameroun ?",
      "Plan de contenu LinkedIn pour KNB",
      "Analyse concurrentielle des agences web à Yaoundé",
    ],
    curriculum: ["Marketing digital PME Afrique 2025", "SEO référencement Google algorithme", "Google Ads Meta Ads budget ROI PME", "Content marketing réseaux sociaux", "Email marketing automation conversion"],
  },
  {
    id: "community_manager_agent", name: "CommunityManagerAgent", role: "Community Manager", pole: "Business", Icon: Megaphone,
    description: "Réseaux sociaux, contenu, TikTok, LinkedIn, Instagram",
    starters: [
      "5 posts LinkedIn pour présenter les services KNB",
      "Script TikTok 60s : « pourquoi votre PME a besoin d'un site »",
      "Calendrier éditorial sur 4 semaines",
      "Légende Instagram + hashtags pour un projet livré",
    ],
    curriculum: ["Instagram Facebook TikTok engagement Afrique", "WhatsApp Business marketing Cameroun", "Contenu viral Reels Shorts tendances", "Community management gestion de crise", "Calendrier éditorial planification"],
  },
  {
    id: "architecte_agent", name: "ArchitecteAgent", role: "Architecte Logiciel", pole: "Technique", Icon: Building2,
    description: "Architecture, choix tech, scalabilité, sécurité, ADR",
    starters: [
      "Architecture pour une app e-commerce, 1000 utilisateurs",
      "PostgreSQL vs MongoDB pour une plateforme de réservation ?",
      "Rédige un ADR : Next.js vs React SPA",
      "Mesures de sécurité OWASP à implémenter ?",
    ],
    curriculum: ["Architecture microservices vs monolithe", "Design patterns SOLID Clean Architecture", "Scalabilité haute disponibilité", "Sécurité OWASP Top 10 2025", "Infrastructure cloud Vercel Render Firebase"],
  },
  {
    id: "dev_frontend_agent", name: "DevFrontendAgent", role: "Dev Frontend", pole: "Technique", Icon: LayoutTemplate,
    description: "React, Next.js, TypeScript, Tailwind, performance, a11y",
    starters: [
      "Composant carte de service KNB en React + Tailwind",
      "Optimiser le LCP d'une page Next.js sous 2.5s ?",
      "Hook React pour un formulaire de contact",
      "Revue de code : améliorer ce composant React",
    ],
    curriculum: ["React 19 server components hooks", "Next.js 15 App Router performance SEO", "TypeScript 5 strict type safety", "Tailwind CSS composants accessibilité", "Core Web Vitals LCP FID CLS optimisation"],
  },
  {
    id: "dev_backend_agent", name: "DevBackendAgent", role: "Dev Backend", pole: "Technique", Icon: ServerCog,
    description: "Node.js, APIs REST, Prisma, PostgreSQL, Firebase, sécurité",
    starters: [
      "API REST CRUD projets avec Zod + Prisma",
      "Authentification Firebase Auth côté serveur ?",
      "Schéma Prisma pour la gestion de commandes",
      "Stratégie de rate limiting pour une API publique ?",
    ],
    curriculum: ["Node.js 22 LTS API REST architecture", "Prisma ORM PostgreSQL migrations", "JWT OAuth2 authentification sécurité", "Docker déploiement production Node", "WebSocket temps réel Socket.io"],
  },
  {
    id: "dev_mobile_agent", name: "DevMobileAgent", role: "Dev Mobile", pole: "Technique", Icon: Smartphone,
    description: "React Native, Expo, offline-first, iOS/Android, déploiement",
    starters: [
      "App React Native Expo avec navigation + offline",
      "Synchronisation de données offline sur Android ?",
      "Guide de déploiement Play Store étape par étape",
      "Optimiser une app React Native pour la 2G/3G",
    ],
    curriculum: ["React Native Expo SDK nouveautés", "React Native navigation Expo Router", "Optimisation listes FlatList performance", "Mobile Money API MTN MoMo Orange", "PWA vs application native comparaison"],
  },
  {
    id: "devops_agent", name: "DevOpsAgent", role: "DevOps & Déploiement", pole: "Technique", Icon: Rocket,
    description: "CI/CD, GitHub Actions, Vercel, Railway, monitoring, Docker",
    starters: [
      "Pipeline GitHub Actions : Vercel + Railway",
      "Checklist go-live pour la mise en production",
      "Monitoring Sentry pour une app Next.js ?",
      "Dockerfile multi-stage optimisé pour Node.js",
    ],
    curriculum: ["GitHub Actions CI/CD déploiement auto", "Docker Compose production secrets", "Monitoring Grafana Prometheus alertes", "Sécurité DevSecOps SAST DAST", "Render Vercel Railway déploiement gratuit"],
  },
  {
    id: "qa_agent", name: "QAAgent", role: "QA & Tests", pole: "Technique", Icon: FlaskConical,
    description: "Tests unitaires/E2E, recette client, automatisation, qualité",
    starters: [
      "Plan de tests complet pour une app e-commerce",
      "Checklist de recette client pour un site vitrine",
      "Tests E2E Playwright pour un flow d'authentification",
      "Template de rapport de bugs pour client non-technique",
    ],
    curriculum: ["Tests automatisés Playwright Cypress E2E", "TDD BDD Jest Vitest bonnes pratiques", "CI/CD GitHub Actions pipeline qualité", "Tests performance Artillery k6", "Accessibilité WCAG 2.2 audit automatisé"],
  },
  {
    id: "designer_ux_ui_agent", name: "DesignerUXUIAgent", role: "Designer UX/UI", pole: "Créatif", Icon: Palette,
    description: "Wireframes, design systems, UX, accessibilité, palette KNB",
    starters: [
      "Design system complet avec la palette KNB",
      "Wireframe pour la page d'accueil KNB",
      "Feedback UX sur un formulaire de contact",
      "Checklist d'accessibilité WCAG 2.1",
    ],
    curriculum: ["Design system Figma composants tokens", "UX research interviews tests utilisateurs", "Accessibilité WCAG contraste inclusion", "Mobile first responsive design", "Onboarding utilisateur conversion UX"],
  },
  {
    id: "designer_graphique_agent", name: "DesignerGraphiqueAgent", role: "Designer Graphique", pole: "Créatif", Icon: PencilRuler,
    description: "Identité visuelle, logos, chartes graphiques, supports",
    starters: [
      "Brief logo pour une PME de restauration camerounaise",
      "Charte graphique complète pour une startup tech",
      "Quels supports print préparer pour un client BTP ?",
      "Feedback sur une proposition d'identité visuelle",
    ],
    curriculum: ["Identité visuelle logo branding Afrique", "Tendances design graphique 2025", "Typographie web variable fonts", "Psychologie couleurs branding palette", "Formats vectoriels SVG Figma exportation"],
  },
  {
    id: "redacteur_agent", name: "RedacteurAgent", role: "Rédacteur & Copywriter", pole: "Créatif", Icon: PenLine,
    description: "Copywriting SEO, blog, textes web, scripts vidéo",
    starters: [
      "Page d'accueil KNB optimisée SEO",
      "Article de blog : « développement web au Cameroun »",
      "Script TikTok 60s : « app mobile vs site web »",
      "Newsletter mensuelle KNB pour fidéliser",
    ],
    curriculum: ["Copywriting conversion landing page CTA", "SEO rédaction articles blog mots-clés", "Storytelling brand content narration", "Rédaction technique documentation API", "Newsletter email copywriting"],
  },
  {
    id: "chef_projet_agent", name: "ChefDeProjetAgent", role: "Chef de Projet", pole: "Coordination", Icon: ClipboardList,
    description: "Planification Agile, roadmaps, cahier des charges, risques",
    starters: [
      "Roadmap projet de 3 mois pour un site e-commerce",
      "Cahier des charges pour une app de livraison",
      "Plan de sprint avec user stories",
      "Matrice de risques RAID pour un projet web",
    ],
    curriculum: ["Méthode Agile Scrum sprint planning", "Planification WBS estimation charges", "Gestion risques projets techniques", "Communication client reporting", "Outils projet Notion Trello Jira Linear"],
  },
  {
    id: "support_client_agent", name: "SupportClientAgent", role: "Support Client", pole: "Coordination", Icon: LifeBuoy,
    description: "Relation client, onboarding, réclamations, satisfaction",
    starters: [
      "Email de livraison de projet, professionnel et chaleureux",
      "Guide d'onboarding pour un client peu à l'aise avec le numérique",
      "Réponse à : « le site ne s'affiche pas sur mon téléphone »",
      "Template de suivi de satisfaction post-livraison",
    ],
    curriculum: ["Relation client satisfaction NPS CSAT", "Gestion réclamations clients escalade", "Support technique helpdesk SLA", "Onboarding formation client adoption", "Fidélisation client LTV rétention"],
  },
  {
    id: "finance_agent", name: "FinanceAgent", role: "Finance & Comptabilité", pole: "Coordination", Icon: Wallet,
    description: "Facturation FCFA, budgets, rentabilité, trésorerie, TVA",
    starters: [
      "Facture professionnelle pour un site web à 238 500 FCFA TTC",
      "Analyse de rentabilité d'un projet mobile à 1 500 000 FCFA",
      "Plan de trésorerie prévisionnel sur 6 mois",
      "Seuil de rentabilité mensuel de l'agence",
    ],
    curriculum: ["Comptabilité PME OHADA Cameroun", "Facturation devis TVA Cameroun 2025", "Trésorerie gestion flux cash PME", "Financement startup investisseurs", "Pricing services numériques rentabilité FCFA"],
  },
  {
    id: "reviewer_agent", name: "ReviewerAgent", role: "Reviewer & Veille", pole: "Veille", Icon: ShieldCheck,
    description: "Revue multi-agents, cohérence, go/no-go, veille techno",
    starters: [
      "Revue de cohérence entre les livrables de ce projet",
      "Tendances tech à surveiller pour une agence web africaine ?",
      "Verdict go/no-go sur ce plan de projet",
      "Analyse les contradictions entre les recommandations reçues",
    ],
    curriculum: ["Code review checklist qualité sécurité", "Audit technique dette refactoring", "Documentation technique OpenAPI Swagger", "Recette fonctionnelle acceptance", "Lighthouse PageSpeed audit web"],
  },
];

export const POLES: Pole[] = ["Business", "Technique", "Créatif", "Coordination", "Veille"];

const byName = new Map<string, AgentDef>();
const byId = new Map<string, AgentDef>();
for (const a of AGENTS) { byName.set(a.name, a); byId.set(a.id, a); }
// Aliases used by the engine planner.
const ALIASES: Record<string, string> = { FrontendAgent: "DevFrontendAgent", BackendAgent: "DevBackendAgent" };

export function agentByKey(key: string): AgentDef | undefined {
  return byId.get(key) ?? byName.get(key) ?? byName.get(ALIASES[key] ?? "");
}
export function agentIcon(key: string): LucideIcon {
  return agentByKey(key)?.Icon ?? Bot;
}
