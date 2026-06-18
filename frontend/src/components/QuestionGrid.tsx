// ============================================================
// QuestionGrid — 虚拟滚动卡片网格 + 无限滚动加载
// ============================================================

import { useCallback, useEffect, useRef } from 'react'
import { Empty, Spin } from 'antd'
import { useVirtualizer } from '@tanstack/react-virtual'
import Flashcard from './Flashcard'
import { useAppStore } from '../store'

const COLUMNS = 3
const CARD_HEIGHT = 220
const LOAD_MORE_THRESHOLD = 800 // 距底部多少 px 触发加载

export default function QuestionGrid() {
  const { filteredQuestions, loading, hasMore, loadMore } = useAppStore()

  const rowCount = Math.ceil(filteredQuestions.length / COLUMNS)
  const totalRef = useRef(filteredQuestions.length)
  const loadingMoreRef = useRef(false)

  const getRowItems = useCallback(
    (rowIndex: number) => {
      const start = rowIndex * COLUMNS
      return filteredQuestions.slice(start, start + COLUMNS)
    },
    [filteredQuestions],
  )

  const virtualizer = useVirtualizer({
    count: rowCount || 1,
    getScrollElement: () => document.documentElement,
    estimateSize: () => CARD_HEIGHT,
    overscan: 3,
    // 滚动时检测是否需要加载更多
    onChange: (instance) => {
      if (!hasMore || loading) return
      const el = instance.scrollElement
      if (!el) return
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight

      if (distanceFromBottom < LOAD_MORE_THRESHOLD && !loadingMoreRef.current) {
        loadingMoreRef.current = true
        loadMore().finally(() => { loadingMoreRef.current = false })
      }
    },
  })

  // 数据量变化时强制重新测量
  useEffect(() => {
    if (filteredQuestions.length !== totalRef.current) {
      totalRef.current = filteredQuestions.length
      virtualizer.measure()
    }
  }, [filteredQuestions.length, virtualizer])

  if (loading && filteredQuestions.length === 0) {
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
    <div className="relative w-full">
      <div style={{ height: virtualizer.getTotalSize() }}>
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
      {/* 底部加载指示器 */}
      {loading && filteredQuestions.length > 0 && (
        <div className="flex justify-center py-8">
          <Spin size="default" />
        </div>
      )}
      {!hasMore && filteredQuestions.length > 0 && (
        <p className="text-center text-gray-400 text-sm py-8">
          已展示全部 {filteredQuestions.length} 道题目
        </p>
      )}
    </div>
  )
}
