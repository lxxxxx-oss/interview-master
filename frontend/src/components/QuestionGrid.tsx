// ============================================================
// QuestionGrid — 虚拟滚动卡片网格（窗口级滚动）
// ============================================================

import { useCallback, useEffect, useRef } from 'react'
import { Empty } from 'antd'
import { useVirtualizer } from '@tanstack/react-virtual'
import Flashcard from './Flashcard'
import { useAppStore } from '../store'

const COLUMNS = 3
const CARD_HEIGHT = 220

export default function QuestionGrid() {
  const { filteredQuestions, loading } = useAppStore()

  const rowCount = Math.ceil(filteredQuestions.length / COLUMNS)
  const totalRef = useRef(filteredQuestions.length)

  const getRowItems = useCallback(
    (rowIndex: number) => {
      const start = rowIndex * COLUMNS
      return filteredQuestions.slice(start, start + COLUMNS)
    },
    [filteredQuestions],
  )

  const virtualizer = useVirtualizer({
    count: rowCount || 1, // 防止为 0 时 react-virtual 报错，下方已处理空态
    getScrollElement: () => document.documentElement,
    estimateSize: () => CARD_HEIGHT,
    overscan: 3,
  })

  // 数据量变化时强制重新测量
  useEffect(() => {
    if (filteredQuestions.length !== totalRef.current) {
      totalRef.current = filteredQuestions.length
      virtualizer.measure()
    }
  }, [filteredQuestions.length, virtualizer])

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-[200px] rounded-xl bg-gray-100 animate-pulse" />
        ))}
      </div>
    )
  }

  if (filteredQuestions.length === 0) {
    return <Empty description="No matching questions" className="py-20" />
  }

  return (
    <div className="relative w-full" style={{ height: virtualizer.getTotalSize() }}>
      {virtualizer.getVirtualItems().map((virtualRow) => {
        const items = getRowItems(virtualRow.index)
        return (
          <div
            key={virtualRow.key}
            className="absolute top-0 left-0 w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"
            style={{
              height: CARD_HEIGHT,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            {items.map((q) => (
              <Flashcard key={q.id} question={q} />
            ))}
          </div>
        )
      })}
    </div>
  )
}
