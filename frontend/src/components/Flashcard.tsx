// ============================================================
// Flashcard — 单击进详情，hover 浮现提示按钮（侧边轻量展示）
// ============================================================

import { useState, useRef } from 'react'
import { Card, Tag, Popover, Tooltip } from 'antd'
import {
  BulbOutlined,
  CheckCircleOutlined,
  StarOutlined,
  CheckCircleFilled,
  StarFilled,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { Question, QuestionState } from '../types'
import { useAppStore } from '../store'

const DIFFICULTY_MAP: Record<string, { label: string; color: string }> = {
  easy: { label: 'Easy', color: 'green' },
  medium: { label: 'Medium', color: 'orange' },
  hard: { label: 'Hard', color: 'red' },
}

const CATEGORY_COLORS: Record<string, string> = {
  'Agent基础': '#1677ff',
  'RAG': '#52c41a',
  'MCP协议': '#722ed1',
  'Function Calling': '#fa8c16',
  'Prompt Engineering': '#13c2c2',
  '记忆机制': '#eb2f96',
  '向量检索': '#2f54eb',
  '模型架构': '#fa541c',
}


export default function Flashcard({ question }: { question: Question }) {
  const navigate = useNavigate()
  const diff = DIFFICULTY_MAP[question.difficulty] || DIFFICULTY_MAP.easy
  const [hover, setHover] = useState(false)
  const hintRef = useRef<HTMLButtonElement>(null)

  const { questionStates, setQuestionState } = useAppStore()
  const currentState: QuestionState | undefined = questionStates[question.id]

  const handleDetail = () => navigate(`/question/${question.id}`)

  const handleStateToggle = (e: React.MouseEvent, state: QuestionState) => {
    e.stopPropagation()
    if (currentState === state) {
      setQuestionState(question.id, null)  // cancel
    } else {
      setQuestionState(question.id, state) // set (auto-switches if was other state)
    }
  }

  return (
    <Card
      className="flashcard group relative h-[200px] rounded-xl border border-gray-100
                 transition-all duration-300 hover:shadow-lg hover:-translate-y-1
                 hover:border-blue-200 overflow-visible cursor-pointer"
      bodyStyle={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '16px 20px',
      }}
      onClick={handleDetail}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {/* Tags row */}
      <div className="flex items-center gap-2 flex-wrap">
        <Tag color={diff.color} className="text-xs">{diff.label}</Tag>
        {question.company && (
          <Tag className="text-xs">{question.company}</Tag>
        )}
        <Tag color={CATEGORY_COLORS[question.category] || '#666'} className="text-xs">
          {question.category}
        </Tag>
      </div>

      {/* Title */}
      <div className="flex-1 flex items-center my-2">
        <p className="text-[15px] leading-relaxed text-gray-800 line-clamp-3">
          {question.title}
        </p>
      </div>

      {/* Bottom: state buttons + hint button */}
      <div className="flex items-center justify-between text-xs text-gray-400 relative">
        {/* State buttons — always visible */}
        <div className="flex items-center gap-1">
          <Tooltip title={currentState === 'mastered' ? '取消已学会' : '标记已学会'}>
            <button
              className={`flex items-center gap-0.5 transition-colors duration-200 cursor-pointer border-0 rounded-full px-2 py-1 text-xs font-medium
                ${currentState === 'mastered' ? 'bg-green-50 text-green-500' : 'bg-gray-50 text-gray-400 hover:text-green-500 hover:bg-green-50'}`}
              onClick={(e) => handleStateToggle(e, 'mastered')}
            >
              {currentState === 'mastered' ? <CheckCircleFilled /> : <CheckCircleOutlined />}
            </button>
          </Tooltip>
          <Tooltip title={currentState === 'bookmarked' ? '取消收藏' : '收藏'}>
            <button
              className={`flex items-center gap-0.5 transition-colors duration-200 cursor-pointer border-0 rounded-full px-2 py-1 text-xs font-medium
                ${currentState === 'bookmarked' ? 'bg-amber-50 text-amber-500' : 'bg-gray-50 text-gray-400 hover:text-amber-500 hover:bg-amber-50'}`}
              onClick={(e) => handleStateToggle(e, 'bookmarked')}
            >
              {currentState === 'bookmarked' ? <StarFilled /> : <StarOutlined />}
            </button>
          </Tooltip>
        </div>

        <div className="flex items-center gap-2">
          {/* Hint button — pops up outside the card on hover */}
          <Popover
            trigger="hover"
            placement="bottomRight"
            title={null}
            content={
              <div className="max-w-[300px]">
                <p className="text-gray-900 text-sm mb-2 font-medium">💡 解题提示</p>
                <p className="text-gray-600 text-sm leading-relaxed">{question.hint || '暂无提示'}</p>
              </div>
            }
          >
            <button
              ref={hintRef}
              className={`flex items-center gap-1 text-amber-500 hover:text-amber-600
                         transition-all duration-200 cursor-pointer border-0 bg-amber-50
                         hover:bg-amber-100 rounded-full px-2.5 py-1 text-xs font-medium
                         ${hover ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1'}`}
              onClick={(e) => e.stopPropagation()}
            >
              <BulbOutlined />
              提示
            </button>
          </Popover>
        </div>
      </div>
    </Card>
  )
}
