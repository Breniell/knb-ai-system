"""
agents/devmobileagent_agent.py — Wrapper KnbAgent (v3.1).
"""
from __future__ import annotations
from typing import Any
from app.agents.base import KnbAgent
from app.agents._senior_prompts import SENIOR_PROMPTS
from app.models import ExecutionContext, SubTask


class DevMobileAgent(KnbAgent):
    name = "DevMobileAgent"
    specialty = "React Native, Expo Router, offline-first, Mobile Money MTN/Orange"
    emoji = "📱"
    _system_prompt = SENIOR_PROMPTS.get("DevMobileAgent", "")

    def _fallback_response(self, task: SubTask, context: ExecutionContext) -> dict[str, Any]:
        return {
            "summary": 'Architecture app mobile Expo Router avec navigation par tabs, gestion offline MMKV, intégration Mobile Money sandbox. Taille APK cible < 20 Mo, démarrage à froid < 2.5s.',
            "artifacts": [{'type': 'screen', 'title': 'Écran Home + navigation Expo Router', 'content': "// app/(tabs)/index.tsx\nimport { View, Text, FlatList, RefreshControl } from 'react-native'\nimport { useRouter } from 'expo-router'\nimport { useQuery } from '@tanstack/react-query'\nimport { useNetInfo } from '@react-native-community/netinfo'\nimport { getProjects } from '@/services/projects'\nimport { ProjectCard } from '@/components/ProjectCard'\nimport { OfflineBanner } from '@/components/OfflineBanner'\n\nexport default function HomeScreen() {\n  const router = useRouter()\n  const { isConnected } = useNetInfo()\n  const { data, isLoading, refetch, isRefetching } = useQuery({\n    queryKey: ['projects'],\n    queryFn: getProjects,\n    staleTime: 5 * 60_000,\n  })\n\n  return (\n    <View className='flex-1 bg-gray-50'>\n      {!isConnected && <OfflineBanner />}\n      <FlatList\n        data={data?.projects ?? []}\n        keyExtractor={item => item.id}\n        renderItem={({ item }) => (\n          <ProjectCard project={item}\n            onPress={() => router.push(`/project/${item.id}`)} />\n        )}\n        refreshControl={\n          <RefreshControl refreshing={isRefetching} onRefresh={refetch} />}\n        ListEmptyComponent={\n          isLoading ? null : (\n            <Text className='text-center text-gray-500 mt-12'>\n              Aucun projet. Créez le premier !\n            </Text>)}\n      />\n    </View>\n  )\n}"}],
            "followups": ["L'app doit-elle fonctionner 100% hors-ligne ou juste tolérer les coupures courtes ?", 'Intégration Mobile Money en phase 1 ou phase 2 ?', 'Cibler Android seulement (80% du marché Cameroun) ou iOS aussi ?'],
            "score": 0.78,
        }
