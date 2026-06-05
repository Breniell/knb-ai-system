"""
tools/learning_resources.py — Curriculum d'apprentissage autonome par agent.

Ce fichier définit les sources concrètes que chaque agent doit étudier pour
atteindre le niveau senior dans son domaine. Les ressources sont :
  - Des documentations officielles (MDN, React, Next.js, Prisma...)
  - Des formations gratuites et certifications (Google, Meta, HubSpot...)
  - Des ressources contextuelles Afrique / Cameroun (OHADA, DGI, Mobile Money)
  - Des blogs et références techniques de premier plan

Structure :
  - topic : nom du sujet
  - urls : liste de sources à scraper
  - synthesis_prompt : ce que l'agent doit extraire de ce sujet
  - depth : "foundation" | "intermediate" | "advanced"
  - freshness_hours : fréquence de re-formation (48h pour tech qui évolue vite,
    720h=30j pour des sujets stables)

Le LearningEngine scrape ces sources, synthétise avec le LLM, et stocke dans
Firestore — enrichissant le contexte de chaque agent à chaque appel de tâche.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LearningResource:
    topic: str
    urls: list[str]
    synthesis_prompt: str
    depth: str = "intermediate"
    freshness_hours: int = 168  # 7 jours par défaut


@dataclass
class AgentCurriculum:
    agent_name: str
    resources: list[LearningResource]
    certifications: list[dict[str, str]] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# PÔLE TECHNIQUE
# ═══════════════════════════════════════════════════════════════════════════════

ARCHITECTE_RESOURCES = AgentCurriculum(
    agent_name="ArchitecteAgent",
    resources=[
        LearningResource(
            topic="12-factor-app-patterns",
            urls=["https://12factor.net/fr/"],
            synthesis_prompt="Extrais les 12 principes d'apps cloud-native avec leur application pratique pour une PME.",
            depth="foundation",
            freshness_hours=720,
        ),
        LearningResource(
            topic="architecture-decision-records",
            urls=[
                "https://adr.github.io/",
                "https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions",
            ],
            synthesis_prompt="Extrais le template ADR (contexte, décision, alternatives, conséquences) avec exemples.",
            depth="intermediate",
            freshness_hours=720,
        ),
        LearningResource(
            topic="postgresql-vs-mongodb-tradeoffs",
            urls=[
                "https://www.prisma.io/dataguide/intro/comparing-database-types",
                "https://www.mongodb.com/compare/mongodb-postgresql",
            ],
            synthesis_prompt="Critères concrets pour choisir entre PostgreSQL et MongoDB selon le type de données et le volume.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="vercel-railway-render-costs",
            urls=[
                "https://vercel.com/docs/pricing",
                "https://docs.railway.app/reference/pricing",
                "https://render.com/pricing",
            ],
            synthesis_prompt="Grille tarifaire réelle (Free/Hobby/Pro) convertie en FCFA, avec cas d'usage PME recommandés.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="owasp-top10-web-2023",
            urls=["https://owasp.org/www-project-top-ten/"],
            synthesis_prompt="Top 10 vulnérabilités web OWASP avec contre-mesures pratiques en Node.js/Next.js.",
            depth="advanced",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "Google Cloud Associate", "url": "https://cloud.google.com/learn/certification", "free": "non"},
        {"name": "AWS Cloud Practitioner", "url": "https://aws.amazon.com/certification/", "free": "non"},
    ],
)

DEV_FRONTEND_RESOURCES = AgentCurriculum(
    agent_name="DevFrontendAgent",
    resources=[
        LearningResource(
            topic="nextjs-app-router-patterns",
            urls=[
                "https://nextjs.org/docs/app",
                "https://nextjs.org/docs/app/building-your-application/routing",
            ],
            synthesis_prompt="Patterns App Router (Server/Client components, layouts, streaming, loading/error states). Exemples concrets TypeScript.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="react-19-new-features",
            urls=[
                "https://react.dev/blog/2024/12/05/react-19",
                "https://react.dev/reference/react",
            ],
            synthesis_prompt="Nouveautés React 19 (Actions, useActionState, useOptimistic, use()) avec exemples pratiques.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="tailwind-best-practices",
            urls=[
                "https://tailwindcss.com/docs/reusing-styles",
                "https://tailwindcss.com/docs/adding-custom-styles",
            ],
            synthesis_prompt="Bonnes pratiques Tailwind : extraction de composants, design tokens, éviter la classe-soup.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="web-core-vitals-optimization",
            urls=[
                "https://web.dev/articles/lcp",
                "https://web.dev/articles/inp",
                "https://web.dev/articles/cls",
            ],
            synthesis_prompt="Techniques d'optimisation LCP, INP, CLS avec mesures et seuils cibles. Spécifique Next.js.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="typescript-strict-patterns",
            urls=[
                "https://www.typescriptlang.org/docs/handbook/2/types-from-types.html",
                "https://www.typescriptlang.org/docs/handbook/utility-types.html",
            ],
            synthesis_prompt="Types utilitaires TypeScript (Partial, Pick, Record, Awaited), narrowing, template literals. Exemples composants React.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="accessibility-wcag-frontend",
            urls=[
                "https://developer.mozilla.org/fr/docs/Web/Accessibility/ARIA",
                "https://www.w3.org/WAI/WCAG21/quickref/",
            ],
            synthesis_prompt="Critères WCAG AA essentiels pour une PME : contraste, focus, ARIA roles, navigation clavier. Check-list en 10 points.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "Meta Front-End Developer Certificate", "url": "https://www.coursera.org/professional-certificates/meta-front-end-developer", "free": "audit gratuit"},
        {"name": "Google UX Design Certificate", "url": "https://grow.google/certificates/ux-design/", "free": "non"},
    ],
)

DEV_BACKEND_RESOURCES = AgentCurriculum(
    agent_name="DevBackendAgent",
    resources=[
        LearningResource(
            topic="prisma-orm-advanced",
            urls=[
                "https://www.prisma.io/docs/orm/prisma-client/queries",
                "https://www.prisma.io/docs/orm/prisma-migrate",
                "https://www.prisma.io/docs/orm/prisma-client/queries/transactions",
            ],
            synthesis_prompt="Prisma avancé : transactions, batch operations, migrations, indexes. Patterns de pagination (cursor vs offset).",
            freshness_hours=336,
        ),
        LearningResource(
            topic="zod-validation-patterns",
            urls=[
                "https://zod.dev/",
                "https://zod.dev/?id=recursive-types",
            ],
            synthesis_prompt="Schémas Zod pour validation API : request bodies, query params, nested objects, erreurs formatées. Exemples Express.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="nodejs-security-best-practices",
            urls=[
                "https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html",
                "https://blog.nodejs.org/en/blog/vulnerability",
            ],
            synthesis_prompt="Sécurité Node.js : injection, rate limiting, headers sécurité (helmet), secrets management. Top 10 vulnérabilités backend.",
            depth="advanced",
            freshness_hours=720,
        ),
        LearningResource(
            topic="restful-api-design",
            urls=[
                "https://restfulapi.net/",
                "https://cloud.google.com/apis/design",
            ],
            synthesis_prompt="Design d'API REST : naming, status codes, pagination, versionning, HATEOAS partiel. Exemples concrets.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="postgresql-performance-indexes",
            urls=[
                "https://www.postgresql.org/docs/current/indexes.html",
                "https://use-the-index-luke.com/sql/preface",
            ],
            synthesis_prompt="Quand créer un index, quel type (B-tree, GIN, GiST), EXPLAIN ANALYZE pour diagnostiquer. Cas PME courants.",
            depth="advanced",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "Meta Back-End Developer Certificate", "url": "https://www.coursera.org/professional-certificates/meta-back-end-developer", "free": "audit gratuit"},
        {"name": "Node.js Application Developer (OpenJS)", "url": "https://openjsf.org/certification/", "free": "non"},
    ],
)

DEV_MOBILE_RESOURCES = AgentCurriculum(
    agent_name="DevMobileAgent",
    resources=[
        LearningResource(
            topic="expo-router-navigation",
            urls=[
                "https://docs.expo.dev/router/introduction/",
                "https://docs.expo.dev/router/advanced/tabs/",
            ],
            synthesis_prompt="Expo Router : navigation file-based, tabs, stacks, deep links, authentification guards. Exemples TypeScript.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="react-native-offline-first",
            urls=[
                "https://reactnative.dev/docs/network",
                "https://docs.expo.dev/versions/latest/sdk/sqlite/",
                "https://github.com/mrousavy/react-native-mmkv",
            ],
            synthesis_prompt="Stratégies offline-first React Native : MMKV pour KV storage, SQLite pour data relationnelle, sync patterns, queue d'actions offline.",
            depth="advanced",
            freshness_hours=336,
        ),
        LearningResource(
            topic="mtn-momo-api-integration",
            urls=[
                "https://momodeveloper.mtn.com/",
                "https://momodeveloper.mtn.com/api-documentation",
            ],
            synthesis_prompt="MTN MoMo API : sandbox setup, collections (request to pay), disbursements, webhooks, gestion des erreurs. Flux complet React Native.",
            depth="advanced",
            freshness_hours=720,
        ),
        LearningResource(
            topic="app-store-play-store-deployment",
            urls=[
                "https://docs.expo.dev/distribution/app-stores/",
                "https://docs.expo.dev/build/introduction/",
            ],
            synthesis_prompt="Déploiement App Store / Play Store via EAS Build : configuration, assets requis (icons, splash), review guidelines, signing.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "Meta iOS & Android Certificate", "url": "https://www.coursera.org/professional-certificates/meta-ios-developer", "free": "audit gratuit"},
    ],
)

QA_RESOURCES = AgentCurriculum(
    agent_name="QAAgent",
    resources=[
        LearningResource(
            topic="playwright-e2e-testing",
            urls=[
                "https://playwright.dev/docs/intro",
                "https://playwright.dev/docs/best-practices",
            ],
            synthesis_prompt="Playwright : setup, page object model, fixtures, assertions, visual testing. Stratégie pour CI/CD. Exemples TypeScript.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="test-pyramid-strategy",
            urls=[
                "https://martinfowler.com/articles/practical-test-pyramid.html",
                "https://kentcdodds.com/blog/write-tests",
            ],
            synthesis_prompt="Pyramide de tests : unité / intégration / E2E — proportions recommandées, ce qu'on teste à chaque couche. Anti-patterns.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="vitest-jest-unit-testing",
            urls=[
                "https://vitest.dev/guide/",
                "https://jestjs.io/docs/getting-started",
            ],
            synthesis_prompt="Tests unitaires avec Vitest/Jest : mocks, spies, async testing, coverage. Patterns pour Node.js et React.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "ISTQB Foundation Level", "url": "https://www.istqb.org/certifications/certified-tester-foundation-level", "free": "non"},
        {"name": "Postman API Testing Certification", "url": "https://www.postman.com/certification/", "free": "gratuit"},
    ],
)

DEVOPS_RESOURCES = AgentCurriculum(
    agent_name="DevOpsAgent",
    resources=[
        LearningResource(
            topic="github-actions-ci-cd",
            urls=[
                "https://docs.github.com/en/actions/quickstart",
                "https://docs.github.com/en/actions/deployment/about-deployments/deploying-with-github-actions",
            ],
            synthesis_prompt="GitHub Actions : workflows, jobs, steps, secrets, deployer sur Vercel/Railway. Template complet pour projet Next.js + API Node.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="docker-best-practices",
            urls=[
                "https://docs.docker.com/develop/develop-images/dockerfile_best-practices/",
                "https://docs.docker.com/compose/",
            ],
            synthesis_prompt="Dockerfile multi-stage optimisé, .dockerignore, Docker Compose pour dev local, non-root user, healthcheck.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="vercel-deployment-guide",
            urls=[
                "https://vercel.com/docs/deployments/overview",
                "https://vercel.com/docs/environment-variables",
            ],
            synthesis_prompt="Déploiement Vercel : env vars par environnement, preview deployments, domaines, edge functions vs serverless.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="railway-backend-deployment",
            urls=[
                "https://docs.railway.app/guides/deployments",
                "https://docs.railway.app/guides/databases",
            ],
            synthesis_prompt="Déploiement Railway : PostgreSQL managed, Node.js API, env vars, scaling, monitoring intégré. Coûts en USD.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "GitHub Actions Certification", "url": "https://resources.github.com/learn/certifications/", "free": "gratuit"},
        {"name": "Google Cloud Fundamentals", "url": "https://www.cloudskillsboost.google/", "free": "certains cours gratuits"},
    ],
)


# ═══════════════════════════════════════════════════════════════════════════════
# PÔLE BUSINESS
# ═══════════════════════════════════════════════════════════════════════════════

COMMERCIAL_RESOURCES = AgentCurriculum(
    agent_name="CommercialAgent",
    resources=[
        LearningResource(
            topic="vente-b2b-pme-afrique",
            urls=[
                "https://www.hubspot.com/sales/b2b-sales",
                "https://blog.hubspot.com/sales/sales-qualification",
            ],
            synthesis_prompt="Techniques de vente B2B adaptées PME africaines : qualification BANT simplifiée, objections prix, closing WhatsApp.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="devis-facture-cameroun-ohada",
            urls=[
                "https://www.ohada.com/index.php",
                "https://www.dgi.cm/",
            ],
            synthesis_prompt="Mentions légales obligatoires sur devis/factures au Cameroun : NIU, régime imposition, TVA 19.25%, numérotation OHADA.",
            freshness_hours=2160,  # 90 jours — réglementaire stable
        ),
        LearningResource(
            topic="pricing-agence-web-afrique",
            urls=[
                "https://www.freelancer.com/community/articles/web-design-cost",
                "https://clutch.co/web-designers/pricing-guide",
            ],
            synthesis_prompt="Grille tarifaire agences web Afrique subsaharienne : site vitrine, e-commerce, app mobile. Benchmarks 2024 en FCFA.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "HubSpot Sales Software Certification", "url": "https://academy.hubspot.com/courses/sales-software", "free": "GRATUIT"},
        {"name": "HubSpot Inbound Sales", "url": "https://academy.hubspot.com/courses/inbound-sales", "free": "GRATUIT"},
        {"name": "Salesforce Sales Representative", "url": "https://trailhead.salesforce.com/credentials/salesrepresentative", "free": "gratuit avec Trailhead"},
    ],
)

MARKETING_RESOURCES = AgentCurriculum(
    agent_name="MarketingAgent",
    resources=[
        LearningResource(
            topic="google-ads-fondamentaux",
            urls=[
                "https://skillshop.withgoogle.com/",
                "https://support.google.com/google-ads/answer/6146252",
            ],
            synthesis_prompt="Fondamentaux Google Ads : campagnes Search, Display, types de correspondance, enchères, KPI. Paramétrage pour PME Cameroun.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="meta-ads-manager-afrique",
            urls=[
                "https://www.facebook.com/business/ads",
                "https://www.facebook.com/business/learn/lessons/set-up-facebook-pixel",
            ],
            synthesis_prompt="Meta Ads pour Afrique : ciblage géo Cameroun, audiences Lookalike, pixel setup, campagnes WhatsApp click-to-chat, budgets recommandés FCFA.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="seo-francophone-africa",
            urls=[
                "https://developers.google.com/search/docs/fundamentals/seo-starter-guide",
                "https://moz.com/learn/seo/on-page-factors",
            ],
            synthesis_prompt="SEO technique + éditorial pour PME Afrique francophone : on-page, vitesse, backlinks, recherche mots-clés en français.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="email-marketing-drip",
            urls=[
                "https://mailchimp.com/resources/email-marketing-benchmarks/",
                "https://academy.hubspot.com/courses/email-marketing",
            ],
            synthesis_prompt="Email marketing : taux d'ouverture secteur tech Afrique, séquences drip, A/B testing objets, deliverability.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "Google Digital Garage - Fondamentaux du marketing numérique", "url": "https://learndigital.withgoogle.com/digitalgarage/course/digital-marketing", "free": "GRATUIT + certificat"},
        {"name": "Meta Blueprint - Facebook Ads", "url": "https://www.facebook.com/business/learn", "free": "GRATUIT"},
        {"name": "HubSpot Marketing Software", "url": "https://academy.hubspot.com/courses/marketing-software", "free": "GRATUIT"},
        {"name": "Google Ads Search Certification", "url": "https://skillshop.withgoogle.com/", "free": "GRATUIT"},
        {"name": "Google Analytics Certification", "url": "https://skillshop.withgoogle.com/", "free": "GRATUIT"},
    ],
)

COMMUNITY_RESOURCES = AgentCurriculum(
    agent_name="CommunityManagerAgent",
    resources=[
        LearningResource(
            topic="meta-blueprint-social-media",
            urls=[
                "https://www.facebook.com/business/learn/lessons/facebook-page-basics",
                "https://www.facebook.com/business/learn/lessons/facebook-ads-overview",
            ],
            synthesis_prompt="Algorithmes Facebook/Instagram 2024-2025, best practices de contenu, timing de publication, format Reels vs Feed.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="tiktok-cameroun-best-practices",
            urls=[
                "https://newsroom.tiktok.com/fr-fr/",
                "https://www.tiktok.com/creators/creator-portal/fr-fr/",
            ],
            synthesis_prompt="Stratégie TikTok pour PME Cameroun : formats, hashtags populaires fr-africain, horaires, partnership creators locaux.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="whatsapp-business-marketing",
            urls=[
                "https://www.whatsapp.com/business/",
                "https://developers.facebook.com/docs/whatsapp/",
            ],
            synthesis_prompt="WhatsApp Business : catalog produits, broadcast lists, quick replies, click-to-WhatsApp ads. Stratégie PME Cameroun.",
            freshness_hours=336,
        ),
        LearningResource(
            topic="content-calendar-strategy",
            urls=[
                "https://sproutsocial.com/insights/social-media-content-calendar/",
                "https://hootsuite.com/resources/content-calendar",
            ],
            synthesis_prompt="Créer un calendrier éditorial efficace : piliers de contenu, mix (éducatif/divertissant/promotionnel), outils gratuits (Canva, Buffer free).",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "Meta Blueprint - Certified Community Manager", "url": "https://www.facebook.com/business/learn", "free": "GRATUIT"},
        {"name": "HubSpot Social Media Certification", "url": "https://academy.hubspot.com/courses/social-media", "free": "GRATUIT"},
        {"name": "Hootsuite Social Marketing Certification", "url": "https://education.hootsuite.com/pages/certifications", "free": "GRATUIT"},
    ],
)


# ═══════════════════════════════════════════════════════════════════════════════
# PÔLE CRÉATIF
# ═══════════════════════════════════════════════════════════════════════════════

DESIGNER_UX_RESOURCES = AgentCurriculum(
    agent_name="DesignerUXUIAgent",
    resources=[
        LearningResource(
            topic="ux-research-methods",
            urls=[
                "https://www.nngroup.com/articles/which-ux-research-methods/",
                "https://www.nngroup.com/articles/usability-testing-101/",
            ],
            synthesis_prompt="Méthodes UX research : tests utilisateurs, user interviews, card sorting, tree testing. Adapté budget PME (5 users rule).",
            freshness_hours=720,
        ),
        LearningResource(
            topic="figma-design-system",
            urls=[
                "https://help.figma.com/hc/en-us/categories/360002051613-Design",
                "https://www.figma.com/best-practices/components-styles-and-shared-libraries/",
            ],
            synthesis_prompt="Figma design systems : components, auto-layout, variables, tokens. Structure d'une librairie partagée pour agence.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="mobile-ux-africa-context",
            urls=[
                "https://www.smashingmagazine.com/2017/03/world-wide-web-not-world-wide-wealthy/",
                "https://web.dev/patterns/",
            ],
            synthesis_prompt="UX design pour Afrique : contraintes réseau lent, écrans budget Android, données mobiles limitées. Patterns offline, dark mode, texte large.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "Google UX Design Certificate (Coursera)", "url": "https://www.coursera.org/professional-certificates/google-ux-design", "free": "audit gratuit"},
        {"name": "Nielsen Norman Group UX Certification", "url": "https://www.nngroup.com/ux-certification/", "free": "non"},
    ],
)

DESIGNER_GRAPHIQUE_RESOURCES = AgentCurriculum(
    agent_name="DesignerGraphiqueAgent",
    resources=[
        LearningResource(
            topic="brand-identity-design",
            urls=[
                "https://99designs.com/blog/logo-branding/brand-identity-design/",
                "https://www.canva.com/learn/brand-identity/",
            ],
            synthesis_prompt="Processus de création d'identité visuelle : mood board, exploration, grid de construction logo, tests usage.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="color-theory-psychology",
            urls=[
                "https://www.colormatters.com/color-and-design/basic-color-theory",
                "https://www.interaction-design.org/literature/topics/color-theory",
            ],
            synthesis_prompt="Psychologie des couleurs appliquée au branding PME Afrique. Significations culturelles et perception locale.",
            freshness_hours=2160,
        ),
        LearningResource(
            topic="canva-design-professional",
            urls=[
                "https://designschool.canva.com/",
                "https://www.canva.com/learn/design-elements-principles/",
            ],
            synthesis_prompt="Utilisation de Canva en professionnel : templates personnalisables, kit marque, formats exportation PME, collaboration.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "Canva Design School Certification", "url": "https://designschool.canva.com/", "free": "GRATUIT"},
        {"name": "Adobe Certified Professional", "url": "https://www.adobe.com/certifications.html", "free": "non"},
    ],
)

REDACTEUR_RESOURCES = AgentCurriculum(
    agent_name="RedacteurAgent",
    resources=[
        LearningResource(
            topic="seo-copywriting-fr",
            urls=[
                "https://moz.com/learn/seo/on-page-factors",
                "https://www.semrush.com/blog/seo-copywriting/",
            ],
            synthesis_prompt="Copywriting SEO en français : structure H1/H2, densité mots-clés, meta descriptions, balises alt. Techniques storytelling.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="email-copywriting-conversion",
            urls=[
                "https://copyblogger.com/copywriting/",
                "https://optinmonster.com/email-copywriting-tips/",
            ],
            synthesis_prompt="Copywriting email : formules (PAS, AIDA), objets qui s'ouvrent, CTA efficaces, séquences nurturing. Taux ouverts benchmark secteur.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="writing-african-french-tone",
            urls=[
                "https://www.oif.org/langue-francaise/",
                "https://www.academie-francaise.fr/",
            ],
            synthesis_prompt="Ton du français d'affaires en Afrique francophone : formules de politesse, registres (WhatsApp vs email formel), expressions locales acceptables.",
            freshness_hours=2160,
        ),
    ],
    certifications=[
        {"name": "HubSpot Content Marketing Certification", "url": "https://academy.hubspot.com/courses/content-marketing", "free": "GRATUIT"},
        {"name": "Google Fundamentals of Digital Marketing", "url": "https://learndigital.withgoogle.com/digitalgarage/", "free": "GRATUIT + certificat"},
        {"name": "Copyblogger Copywriting Course", "url": "https://copyblogger.com/copywriting/", "free": "gratuit partiel"},
    ],
)


# ═══════════════════════════════════════════════════════════════════════════════
# PÔLE COORDINATION
# ═══════════════════════════════════════════════════════════════════════════════

CHEF_PROJET_RESOURCES = AgentCurriculum(
    agent_name="ChefDeProjetAgent",
    resources=[
        LearningResource(
            topic="agile-scrum-pme",
            urls=[
                "https://www.scrum.org/resources/scrum-guide",
                "https://www.agilealliance.org/agile101/",
            ],
            synthesis_prompt="Scrum allégé pour PME 2-5 personnes : sprint 1 semaine, daily 10 min, ceremonies légères. Adapter sans over-engineering.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="notion-linear-project-tools",
            urls=[
                "https://www.notion.com/help",
                "https://linear.app/docs",
            ],
            synthesis_prompt="Setup Notion et Linear pour gestion de projet agence web : templates project, issue tracking, roadmaps clients.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="risk-management-raid",
            urls=[
                "https://www.pmi.org/learning/library/risk-management-101-7272",
                "https://www.apm.org.uk/resources/find-a-resource/raid-log/",
            ],
            synthesis_prompt="Matrice RAID (Risques, Actions, Issues, Décisions) : template, exemples PME, fréquence de mise à jour, prioritisation.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="client-communication-agence",
            urls=[
                "https://blog.hubspot.com/agency/client-communication",
                "https://www.smashingmagazine.com/2009/09/six-principles-for-a-client-focused-agency-model/",
            ],
            synthesis_prompt="Gestion relation client agence : onboarding, status reports, validation, gestion des changements. Templates adaptés WhatsApp.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "Google Project Management Certificate", "url": "https://grow.google/certificates/project-management/", "free": "audit partiel gratuit"},
        {"name": "Scrum.org PSPO I (Product Owner)", "url": "https://www.scrum.org/assessments", "free": "20 USD - abordable"},
        {"name": "PMP - Project Management Professional", "url": "https://www.pmi.org/certifications/project-management-pmp", "free": "non"},
    ],
)

FINANCE_RESOURCES = AgentCurriculum(
    agent_name="FinanceAgent",
    resources=[
        LearningResource(
            topic="ohada-comptabilite-cameroun",
            urls=[
                "https://www.ohada.com/index.php",
                "https://www.ohada.org/actu/1218/le-plan-comptable-ohada-syscohada-revise.html",
            ],
            synthesis_prompt="SYSCOHADA révisé : plan comptable, structure bilan/compte de résultat, mentions obligatoires pour PME.",
            depth="advanced",
            freshness_hours=2160,
        ),
        LearningResource(
            topic="fiscalite-cameroun-pme",
            urls=[
                "https://www.dgi.cm/",
                "https://www.minfi.gov.cm/",
            ],
            synthesis_prompt="Fiscalité PME Cameroun : TVA 19,25%, IS 30% (ou 1% CMNR), retenue à la source 5,5%, NIU, déclarations trimestrielles. Checklist obligations.",
            depth="advanced",
            freshness_hours=2160,
        ),
        LearningResource(
            topic="mobile-money-comptabilite",
            urls=[
                "https://momodeveloper.mtn.com/",
                "https://developer.orange.com/apis/orange-money-cameroon",
            ],
            synthesis_prompt="Comptabilisation des transactions Mobile Money (MTN MoMo, Orange Money) : charges de commission, réconciliation, reporting fiscal.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="cash-flow-pme-management",
            urls=[
                "https://www.bpifrance.fr/nos-solutions/nos-outils-et-conseils-en-gestion-financiere",
                "https://hbr.org/topic/subject/cash-flow",
            ],
            synthesis_prompt="Gestion trésorerie PME : tableau de flux, DSO, BFR, alerte trésorerie, scénarios stress test. Méthodes simples pour non-financier.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "ACCA Certificate in Business and Technology", "url": "https://www.accaglobal.com/gb/en/qualifications/foundations-in-accountancy/foundations-certificate-in-accounting.html", "free": "non"},
        {"name": "Coursera Financial Accounting (Wharton)", "url": "https://www.coursera.org/learn/wharton-accounting", "free": "audit gratuit"},
    ],
)

SUPPORT_RESOURCES = AgentCurriculum(
    agent_name="SupportClientAgent",
    resources=[
        LearningResource(
            topic="customer-success-metrics",
            urls=[
                "https://www.hubspot.com/customer-success",
                "https://academy.hubspot.com/courses/customer-service",
            ],
            synthesis_prompt="Métriques Customer Success : NPS, CSAT, CES, churn rate. Setup simple, interprétation, actions correctives.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="whatsapp-support-pme",
            urls=[
                "https://www.whatsapp.com/business/features",
                "https://faq.whatsapp.com/en/android/23756523/",
            ],
            synthesis_prompt="WhatsApp Business pour support PME : messages automatiques (absent, bienvenue), quick replies, labels, catalog. Meilleures pratiques.",
            freshness_hours=720,
        ),
        LearningResource(
            topic="onboarding-client-digital",
            urls=[
                "https://www.helpscout.com/blog/customer-onboarding/",
                "https://userpilot.com/blog/customer-onboarding-process/",
            ],
            synthesis_prompt="Process onboarding client agence web/mobile : séquence emails/messages, points de contact J0-J30, checkpoints succès.",
            freshness_hours=720,
        ),
    ],
    certifications=[
        {"name": "HubSpot Customer Service Certification", "url": "https://academy.hubspot.com/courses/customer-service", "free": "GRATUIT"},
        {"name": "Freshdesk Support Certification", "url": "https://freshdesk.com/certification/", "free": "GRATUIT"},
    ],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Registre global
# ═══════════════════════════════════════════════════════════════════════════════

ALL_CURRICULA: dict[str, AgentCurriculum] = {
    "ArchitecteAgent": ARCHITECTE_RESOURCES,
    "DevFrontendAgent": DEV_FRONTEND_RESOURCES,
    "DevBackendAgent": DEV_BACKEND_RESOURCES,
    "DevMobileAgent": DEV_MOBILE_RESOURCES,
    "QAAgent": QA_RESOURCES,
    "DevOpsAgent": DEVOPS_RESOURCES,
    "CommercialAgent": COMMERCIAL_RESOURCES,
    "MarketingAgent": MARKETING_RESOURCES,
    "CommunityManagerAgent": COMMUNITY_RESOURCES,
    "DesignerUXUIAgent": DESIGNER_UX_RESOURCES,
    "DesignerGraphiqueAgent": DESIGNER_GRAPHIQUE_RESOURCES,
    "RedacteurAgent": REDACTEUR_RESOURCES,
    "ChefDeProjetAgent": CHEF_PROJET_RESOURCES,
    "FinanceAgent": FINANCE_RESOURCES,
    "SupportClientAgent": SUPPORT_RESOURCES,
}


def get_curriculum(agent_name: str) -> AgentCurriculum | None:
    return ALL_CURRICULA.get(agent_name)


def list_all_topics() -> dict[str, list[str]]:
    """Retourne le plan de formation complet pour info/debug."""
    return {
        name: [r.topic for r in c.resources]
        for name, c in ALL_CURRICULA.items()
    }


def get_free_certifications() -> dict[str, list[dict[str, str]]]:
    """Retourne uniquement les certifications gratuites par agent."""
    result = {}
    for name, curriculum in ALL_CURRICULA.items():
        free = [c for c in curriculum.certifications if "GRATUIT" in c.get("free", "")]
        if free:
            result[name] = free
    return result
