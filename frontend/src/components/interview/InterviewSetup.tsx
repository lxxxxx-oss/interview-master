// ============================================================
// InterviewSetup — 面试开始前的配置面板
// ============================================================

import { Card, Radio, Select, Button, Space } from 'antd'
import {
  PlayCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import type { Difficulty, StartInterviewParams } from '../../types'

interface Props {
  onStart: (params: StartInterviewParams) => void
}

const DIFF_OPTIONS: { value: Difficulty; label: string; desc: string }[] = [
  { value: 'easy', label: '🟢 初级', desc: '基础概念题，适合入门自测' },
  { value: 'medium', label: '🟡 中级', desc: '原理与流程题，检验理解深度' },
  { value: 'hard', label: '🔴 高级', desc: '架构设计与对比题，模拟高压面试' },
]

export default function InterviewSetup({ onStart }: Props) {
  const handleStart = () => {
    onStart({
      difficulty: 'medium',
      totalQuestions: 3,
    })
  }

  return (
    <div className="max-w-2xl mx-auto pt-16 pb-20">
      {/* 头部 */}
      <div className="text-center mb-10">
        <ThunderboltOutlined
          style={{ fontSize: 48, color: '#1677ff', marginBottom: 16 }}
        />
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          🤖 AI 模拟面试
        </h1>
        <p className="text-gray-500">
          基于 LangGraph 工作流的 Agentic 面试体验 —
          AI 面试官会出题、评估、追问，模拟真实面试场景
        </p>
      </div>

      {/* 配置卡片 */}
      <Card className="rounded-xl shadow-sm mb-8">
        <div className="space-y-6">
          {/* 难度选择 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              选择难度
            </label>
            <Radio.Group
              defaultValue="medium"
              className="w-full"
            >
              <Space direction="vertical" className="w-full">
                {DIFF_OPTIONS.map((opt) => (
                  <Radio
                    key={opt.value}
                    value={opt.value}
                    className="w-full p-3 rounded-lg border border-gray-100
                               hover:border-blue-200 transition-colors"
                  >
                    <span className="font-medium">{opt.label}</span>
                    <span className="text-gray-400 text-sm ml-2">
                      — {opt.desc}
                    </span>
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          </div>

          {/* 题数选择 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              面试题数
            </label>
            <Select
              defaultValue={3}
              className="w-full"
              options={[
                { value: 1, label: '1 题 — 快速体验' },
                { value: 3, label: '3 题 — 标准面试' },
                { value: 5, label: '5 题 — 深度模拟' },
              ]}
            />
          </div>
        </div>
      </Card>

      {/* 开始按钮 */}
      <div className="text-center">
        <Button
          type="primary"
          size="large"
          icon={<PlayCircleOutlined />}
          onClick={handleStart}
          className="px-12 h-12 text-lg rounded-xl"
        >
          开始面试
        </Button>
        <p className="text-xs text-gray-400 mt-3">
          面试过程中可随时结束，当前版本数据不保存
        </p>
      </div>
    </div>
  )
}
