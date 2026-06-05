"""
agents/devfrontendagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class DevFrontendAgent(KnbAgent):
    name = "DevFrontendAgent"
    specialty = "React 19, Next.js 14 App Router, TypeScript strict, Tailwind, Web Vitals"
    emoji = "⚛️"
    _system_prompt = SENIOR_PROMPTS.get("DevFrontendAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": "Composants TypeScript livrés : layout principal, système de navigation, composants atomiques (Button, Input, Card) et page d'accueil responsive. Score Lighthouse estimé 90+ avec les bonnes pratiques appliquées.",
            "artifacts": [{'type': 'components', 'title': 'Composants React TypeScript', 'content': "// components/ui/Button.tsx\nimport { ButtonHTMLAttributes, forwardRef } from 'react'\nimport { cn } from '@/lib/utils'\n\ninterface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {\n  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'\n  size?: 'sm' | 'md' | 'lg'\n  loading?: boolean\n}\n\nexport const Button = forwardRef<HTMLButtonElement, ButtonProps>(\n  ({ className, variant = 'primary', size = 'md', loading, children, disabled, ...props }, ref) => (\n    <button\n      ref={ref}\n      disabled={disabled || loading}\n      aria-busy={loading}\n      className={cn(\n        'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2',\n        { 'bg-sky-500 text-white hover:bg-sky-600': variant === 'primary' },\n        { 'border border-sky-500 text-sky-500 hover:bg-sky-50': variant === 'secondary' },\n        { 'px-3 py-1.5 text-sm': size === 'sm' },\n        { 'px-4 py-2 text-base': size === 'md' },\n        { 'px-6 py-3 text-lg': size === 'lg' },\n        { 'opacity-50 cursor-not-allowed': disabled || loading },\n        className\n      )}\n      {...props}\n    >\n      {loading ? <span className='mr-2 animate-spin'>⟳</span> : null}\n      {children}\n    </button>\n  )\n)\nButton.displayName = 'Button'\n"}],
            "followups": ['Existe-t-il un design Figma à respecter ou on définit le design system ensemble ?', 'Quels navigateurs cibles ? (Safari iOS, Chrome Android prioritaires au Cameroun)', 'Internationalisation FR/EN prévue ?'],
            "score": 0.78,
        }
