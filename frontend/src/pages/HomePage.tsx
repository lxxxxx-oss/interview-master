// ============================================================
// HomePage — FilterBar + QuestionGrid（对接真实后端）
// ============================================================

import { useEffect } from 'react'
import FilterBar from '../components/FilterBar'
import QuestionGrid from '../components/QuestionGrid'
import { useAppStore } from '../store'

export default function HomePage() {
  const { fetchFilterOptions, fetchQuestions } = useAppStore()

  useEffect(() => {
    fetchFilterOptions()
    fetchQuestions()
  }, [])

  return (
    <div className="pb-20">
      {/* 页面标题 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          📋 面试题库
        </h1>
        <p className="text-gray-500 mt-1">
         覆盖大厂 Agent / RAG / MCP / LLM 等方向面试真题 — 点击卡片查看提示与答案
        </p>
      </div>

      <FilterBar />
      <QuestionGrid />
    </div>
  )
}
