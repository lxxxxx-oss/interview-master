// ============================================================
// HomePage — FilterBar + QuestionGrid（对接真实后端）
// ============================================================

import { useEffect } from 'react'
import FilterBar from '../components/FilterBar'
import QuestionGrid from '../components/QuestionGrid'
import { useAppStore } from '../store'

export default function HomePage() {
  const { fetchFilterOptions, fetchQuestions, loadQuestionStates } = useAppStore()

  useEffect(() => {
    loadQuestionStates()
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
          聚焦 Agent / RAG / MCP / LLM 等方向高频面试真题，点击卡片查看提示与标准答案
        </p>
        <p className="text-gray-400 text-xs mt-1">
          题目来源于网络公开面经，答案由 AI 生成仅供参考，未经严格校验，如有错误欢迎指正。如有侵权请联系删除。
        </p>
      </div>

      <FilterBar />
      <QuestionGrid />
    </div>
  )
}
