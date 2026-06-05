"""
agents/_quality_rubric.py — Critères de qualité par type d'agent.

Chaque agent compare son draft à une grille de critères concrets avant
de soumettre. Cela force la production de livrables réellement utilisables
plutôt que de fluff générique.

Les rubriques sont volontairement courtes (5-7 critères) et binaires :
chaque critère est SOIT respecté SOIT non. Le score = nb critères OK / total.
Un draft sous le seuil minimum déclenche une révision automatique.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityRubric:
    """Grille de critères + seuil pour un agent."""
    name: str
    criteria: tuple[str, ...]
    min_pass_ratio: float = 0.7  # 70% de critères validés pour passer


# ═══════════════════════════════════════════════════════════════════════════════
# Rubriques par agent
# ═══════════════════════════════════════════════════════════════════════════════

# Règles génériques (héritées par tous)
_BASE_CRITERIA = (
    "Le summary fait moins de 4 phrases et résume précisément la valeur livrée.",
    "Au moins 1 artefact est présent et contient un livrable concret (pas un placeholder).",
    "Aucun artefact ne contient '[À COMPLÉTER]' '[TODO]' ou du texte générique sans valeur.",
    "Les followups (max 3) sont des questions/actions actionnables, pas des banalités.",
)

RUBRICS: dict[str, QualityRubric] = {

    # ── DEV ─────────────────────────────────────────────────────────────────
    "DevFrontendAgent": QualityRubric(
        name="DevFrontendAgent",
        criteria=_BASE_CRITERIA + (
            "Le code TypeScript/React est syntaxiquement complet (imports, exports, types).",
            "Au moins un composant fonctionnel avec props typées est livré.",
            "L'accessibilité (aria, sémantique HTML) ou les Core Web Vitals sont adressés.",
            "Les classes Tailwind utilisent la palette KNB ou un design system cohérent.",
        ),
    ),
    "DevBackendAgent": QualityRubric(
        name="DevBackendAgent",
        criteria=_BASE_CRITERIA + (
            "Le code Node/TypeScript inclut imports, types et gestion d'erreurs.",
            "Au moins un endpoint REST avec validation Zod (ou équivalent) est livré.",
            "Les schémas de base de données (Prisma/SQL) sont concrets, pas des stubs.",
            "Sécurité minimale présente : auth, validation input, ou rate limiting.",
        ),
    ),
    "DevMobileAgent": QualityRubric(
        name="DevMobileAgent",
        criteria=_BASE_CRITERIA + (
            "Le code React Native/Expo est complet (imports, navigation, état).",
            "L'aspect offline-first ou réseau dégradé est pris en compte.",
            "Au moins une intégration Mobile Money (MTN MoMo / Orange Money) si pertinent.",
        ),
    ),
    "ArchitecteAgent": QualityRubric(
        name="ArchitecteAgent",
        criteria=_BASE_CRITERIA + (
            "L'architecture est décrite avec stack précise (frameworks, versions, services).",
            "Les coûts d'hébergement sont chiffrés en FCFA/mois.",
            "Au moins un ADR (Architecture Decision Record) justifie un choix clé.",
            "La sécurité (OWASP) et la scalabilité sont adressées explicitement.",
        ),
    ),
    "QAAgent": QualityRubric(
        name="QAAgent",
        criteria=_BASE_CRITERIA + (
            "Un plan de tests structuré (modules × cas) est livré.",
            "Les flows critiques (auth, paiement, données) sont couverts.",
            "Une checklist de recette client en français simple est fournie.",
        ),
    ),
    "DevOpsAgent": QualityRubric(
        name="DevOpsAgent",
        criteria=_BASE_CRITERIA + (
            "Un pipeline CI/CD complet (YAML) ou Dockerfile concret est livré.",
            "Le coût mensuel estimé est en FCFA et compatible budget KNB.",
            "Une stratégie de monitoring/alerting est précisée.",
        ),
    ),

    # ── CRÉATIF ─────────────────────────────────────────────────────────────
    "DesignerUXUIAgent": QualityRubric(
        name="DesignerUXUIAgent",
        criteria=_BASE_CRITERIA + (
            "Au moins un wireframe (décrit en texte structuré) ou flow utilisateur est livré.",
            "Les tokens du design system (couleurs, typo, spacing) sont concrets.",
            "L'accessibilité (contraste, navigation clavier) est adressée.",
        ),
    ),
    "DesignerGraphiqueAgent": QualityRubric(
        name="DesignerGraphiqueAgent",
        criteria=_BASE_CRITERIA + (
            "L'identité visuelle inclut palette + typographie + usage (logos, mockups).",
            "Les choix sont justifiés par psychologie marque / cible KNB.",
        ),
    ),
    "RedacteurAgent": QualityRubric(
        name="RedacteurAgent",
        criteria=_BASE_CRITERIA + (
            "Le copy est en français correct, prêt à publier (pas un brief).",
            "Le ton et le CTA sont adaptés à la cible/canal (LinkedIn, SEO, email, etc.).",
            "Si SEO : mots-clés intégrés naturellement, structure H1/H2 explicite.",
        ),
    ),

    # ── BUSINESS ────────────────────────────────────────────────────────────
    "CommercialAgent": QualityRubric(
        name="CommercialAgent",
        criteria=_BASE_CRITERIA + (
            "Tout montant est en FCFA avec TVA 19,25 % séparée.",
            "Le devis ou email est prêt à envoyer (entête + corps + signature KNB).",
            "Une réponse aux objections principales (prix, délais, confiance) est anticipée.",
        ),
    ),
    "MarketingAgent": QualityRubric(
        name="MarketingAgent",
        criteria=_BASE_CRITERIA + (
            "La stratégie a un objectif chiffré (leads, CA, abonnés) sur une période donnée.",
            "Les canaux sont priorisés selon le budget en FCFA.",
            "Au moins une mesure de ROI/KPI concrète est définie.",
        ),
    ),
    "CommunityManagerAgent": QualityRubric(
        name="CommunityManagerAgent",
        criteria=_BASE_CRITERIA + (
            "Un calendrier éditorial (semaine ou mois) avec dates + canaux + formats est livré.",
            "Au moins un post publishable (pas un brief) avec hashtags et CTA.",
            "Les formats sont adaptés aux usages Cameroun (WhatsApp, TikTok, Facebook).",
        ),
    ),

    # ── COORDINATION ────────────────────────────────────────────────────────
    "ChefDeProjetAgent": QualityRubric(
        name="ChefDeProjetAgent",
        criteria=_BASE_CRITERIA + (
            "Une roadmap avec phases + sprints + livrables datables est livrée.",
            "Au moins 3 risques sont identifiés avec mitigation concrète.",
            "Les jalons de validation client sont explicites.",
        ),
    ),
    "SupportClientAgent": QualityRubric(
        name="SupportClientAgent",
        criteria=_BASE_CRITERIA + (
            "Au moins un script de réponse complet (pas un template vide).",
            "Le canal préféré du client KNB (WhatsApp) est pris en compte.",
            "Une stratégie de mesure (NPS, CSAT) est suggérée.",
        ),
    ),
    "FinanceAgent": QualityRubric(
        name="FinanceAgent",
        criteria=_BASE_CRITERIA + (
            "Tous les montants sont en FCFA avec ventilation HT / TVA 19,25 % / TTC.",
            "Les obligations fiscales camerounaises (NIU, retenue 5,5 %) sont mentionnées si pertinent.",
            "Un échéancier ou plan de trésorerie chiffré est livré si demandé.",
        ),
    ),

    # ── VEILLE ──────────────────────────────────────────────────────────────
    "ReviewerAgent": QualityRubric(
        name="ReviewerAgent",
        criteria=(
            "Le verdict (go / go_with_minor_fixes / no_go) est explicite.",
            "Au moins 1 contradiction OU 1 risque inter-agent est cité, avec preuve depuis les artefacts.",
            "Le plan d'action priorise les corrections (P1/P2/P3).",
            "Chaque correction P1 vise un artefact identifié par son agent + titre.",
            "Aucun élément n'est inventé (toutes les affirmations s'appuient sur les artefacts reçus).",
        ),
        min_pass_ratio=0.8,
    ),
}

# Rubrique générique pour agents sans spec dédiée
_DEFAULT_RUBRIC = QualityRubric(
    name="default",
    criteria=_BASE_CRITERIA + (
        "Le livrable est immédiatement utilisable par un client KNB.",
    ),
)


def get_rubric(agent_name: str) -> QualityRubric:
    return RUBRICS.get(agent_name, _DEFAULT_RUBRIC)


def render_rubric_for_prompt(rubric: QualityRubric) -> str:
    """Formate la rubrique pour injection dans le prompt d'auto-critique."""
    bullets = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(rubric.criteria))
    return (
        f"CRITÈRES DE QUALITÉ (seuil de validation : "
        f"{int(rubric.min_pass_ratio * 100)}%) :\n{bullets}"
    )
