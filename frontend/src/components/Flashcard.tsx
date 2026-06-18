// ============================================================
// Flashcard — 单击进详情，hover 浮现提示按钮（侧边轻量展示）
// ============================================================

import { useState, useRef } from 'react'
import { Card, Tag, Popover, Popconfirm, message } from 'antd'
import {
  BulbOutlined,
  DeleteOutlined,
  EditOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { Question } from '../types'
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

const SOURCE_ICON: Record<string, string> = {
  local: '📝',
  nowcoder: '🌐',
  hub: '📋',
}

export default function Flashcard({ question }: { question: Question }) {
  const navigate = useNavigate()
  const { deleteQuestion } = useAppStore()
  const diff = DIFFICULTY_MAP[question.difficulty] || DIFFICULTY_MAP.easy
  const [hover, setHover] = useState(false)
  const hintRef = useRef<HTMLButtonElement>(null)

  const handleDetail = () => navigate(`/question/${question.id}`)

  const handleDeleteConfirm = async () => {
    try {
      await deleteQuestion(question.id)
      message.success('Deleted')
    } catch (err: any) {
      message.error(err.message || 'Delete failed')
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

      {/* Bottom: source + admin actions + hint button that floats up on hover */}
      <div className="flex items-center justify-between text-xs text-gray-400 relative">
        <span>{SOURCE_ICON[question.source] || '📝'} {question.source === 'local' ? '收录' : question.source === 'hub' ? 'Hub' : '牛客'}</span>

        <div className="flex items-center gap-2">
          {/* Admin — visible on hover */}
          <span className={`inline-flex items-center gap-1 transition-opacity duration-200 ${hover ? 'opacity-100' : 'opacity-0'}`}>
            <button
              className="text-gray-400 hover:text-blue-400 transition-colors cursor-pointer border-0 bg-transparent p-0"
              onClick={(e) => { e.stopPropagation(); navigate(`/question/${question.id}`) }}
            >
              <EditOutlined />
            </button>
            <Popconfirm
              title="Delete?"
              onConfirm={handleDeleteConfirm}
              okText="Delete"
              okType="danger"
              cancelText="Cancel"
            >
              <button
                className="text-gray-400 hover:text-red-400 transition-colors cursor-pointer border-0 bg-transparent p-0"
                onClick={(e) => e.stopPropagation()}
              >
                <DeleteOutlined />
              </button>
            </Popconfirm>
          </span>

          {/* Hint button — pops up outside the card on hover */}
          <Popover
            trigger="click"
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
              Hint
            </button>
          </Popover>
        </div>
      </div>
    </Card>
  )
}
