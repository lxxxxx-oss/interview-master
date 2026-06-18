// ============================================================
// HomePage — FilterBar + QuestionGrid（对接真实后端）
// ============================================================

import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from 'antd'
import { ShakeOutlined } from '@ant-design/icons'
import FilterBar from '../components/FilterBar'
import QuestionGrid from '../components/QuestionGrid'
import { useAppStore } from '../store'

export default function HomePage() {
  const { fetchFilterOptions, fetchQuestions, loadQuestionStates, filteredQuestions } = useAppStore()
  const navigate = useNavigate()

  useEffect(() => {
    loadQuestionStates()
    fetchFilterOptions()
    fetchQuestions()
  }, [])

  const goToRandom = useCallback(() => {
    if (filteredQuestions.length === 0) return
    const randomIdx = Math.floor(Math.random() * filteredQuestions.length)
    navigate(`/question/${filteredQuestions[randomIdx].id}`)
  }, [filteredQuestions, navigate])

  return (
    <div className="pb-20">
      {/* 页面标题 */}
      <div className="mb-6 flex items-start justify-between">
        <div>
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
        <Button
          icon={<ShakeOutlined />}
          onClick={goToRandom}
          className="mt-1 shrink-0 rounded-lg"
        >
          随机一题
        </Button>
      </div>

      <FilterBar />
      <QuestionGrid />
    </div>
  )
}
