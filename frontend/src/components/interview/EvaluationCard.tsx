// ============================================================
// EvaluationCard — 每题之后的评估结果展示
// ============================================================

import { Card, Tag, Progress } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import type { InterviewEvaluation } from '../../types'

interface Props {
  evaluation: InterviewEvaluation
}

function scoreColor(s: number): string {
  if (s >= 80) return '#52c41a'
  if (s >= 50) return '#faad14'
  return '#ff4d4f'
}

export default function EvaluationCard({ evaluation }: Props) {
  const { score, keywordsMatched, missingKeywords, coverage } = evaluation

  return (
    <div className="flex justify-center mb-4">
      <Card
        size="small"
        className="rounded-xl shadow-sm border-blue-100 max-w-lg w-full"
        title={
          <span className="flex items-center gap-2 text-sm">
            <TrophyOutlined style={{ color: scoreColor(score) }} />
            本回答评估
          </span>
        }
      >
        {/* 分数 */}
        <div className="text-center mb-4">
          <Progress
            type="circle"
            percent={score}
            size={80}
            strokeColor={scoreColor(score)}
            format={(p) => (
              <span style={{ fontSize: 20, fontWeight: 700, color: scoreColor(score!) }}>
                {p}
              </span>
            )}
          />
          <div className="text-xs text-gray-400 mt-1">
            语义覆盖度 {Math.round(coverage * 100)}%
          </div>
        </div>

        {/* 命中关键词 */}
        {keywordsMatched.length > 0 && (
          <div className="mb-3">
            <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              命中关键词
            </div>
            <div className="flex flex-wrap gap-1">
              {keywordsMatched.map((kw) => (
                <Tag key={kw} color="green" className="text-xs">
                  {kw}
                </Tag>
              ))}
            </div>
          </div>
        )}

        {/* 遗漏关键词 */}
        {missingKeywords.length > 0 && (
          <div>
            <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
              <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
              遗漏关键词
            </div>
            <div className="flex flex-wrap gap-1">
              {missingKeywords.map((kw) => (
                <Tag key={kw} color="red" className="text-xs">
                  {kw}
                </Tag>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
