// ============================================================
// InterviewChat — 主聊天界面（消息列表 + 输入区 + SSE 流消费）
// ============================================================

import { useEffect, useRef, useState } from 'react'
import { Input, Button, Tag, Space, message } from 'antd'
import {
  SendOutlined,
  StopOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import { useInterviewStore } from '../../store/interviewStore'
import ChatBubble from './ChatBubble'
import EvaluationCard from './EvaluationCard'

const { TextArea } = Input

export default function InterviewChat() {
  const {
    session,
    streamingContent,
    submitAnswer,
    cancelStream,
    resetInterview,
  } = useInterviewStore()

  const [inputValue, setInputValue] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [session?.messages, streamingContent])

  if (!session) return null

  const isBusy =
    session.status === 'evaluating' || session.status === 'streaming_critique'
  const isWaiting = session.status === 'waiting_for_answer'
  const isCompleted = session.status === 'completed'

  const handleSend = async () => {
    const val = inputValue.trim()
    if (!val || isBusy) return

    setInputValue('')
    setSending(true)
    try {
      await submitAnswer(val)
    } catch (e: any) {
      message.error('提交失败：' + (e.message || '网络错误'))
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="max-w-3xl mx-auto h-[calc(100vh-140px)] flex flex-col">
      {/* ─── 顶部状态栏 ───────────────────── */}
      <div className="flex items-center justify-between py-3 px-4 bg-white rounded-xl shadow-sm border border-gray-100 mb-4">
        <Space>
          <Tag color="blue" className="text-sm px-3 py-0.5">
            {session.difficulty === 'easy'
              ? '🟢 初级'
              : session.difficulty === 'medium'
                ? '🟡 中级'
                : '🔴 高级'}
          </Tag>
          <span className="text-sm text-gray-600">
            第 {session.currentQuestionNumber}/{session.totalQuestions} 题
          </span>
          {isBusy && (
            <Tag color="processing" className="text-xs">
              AI 思考中…
            </Tag>
          )}
          {isCompleted && (
            <Tag color="success" className="text-xs">
              面试完成 🎉
            </Tag>
          )}
        </Space>

        <Button
          type="text"
          size="small"
          icon={<CloseOutlined />}
          onClick={resetInterview}
          className="text-gray-400 hover:text-red-500"
        >
          结束面试
        </Button>
      </div>

      {/* ─── 消息列表 ──────────────────────── */}
      <div className="flex-1 overflow-y-auto px-2">
        {session.messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}

        {/* 流式渲染中的消息 */}
        {isBusy && streamingContent && (
          <ChatBubble
            message={{
              id: 'streaming',
              role: 'interviewer',
              content: streamingContent,
              timestamp: Date.now(),
              streaming: true,
            }}
            streaming
          />
        )}

        {/* 评估卡片（答完题后展示） */}
        {session.evaluation &&
          !isBusy &&
          session.messages.length > 0 && (
            <EvaluationCard evaluation={session.evaluation} />
          )}

        {/* 加载指示器 */}
        {isBusy && !streamingContent && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-5 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.15s]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.3s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ─── 输入区 ────────────────────────── */}
      <div className="py-4 px-2">
        {isCompleted ? (
          <div className="text-center">
            <Button
              type="primary"
              onClick={resetInterview}
              className="rounded-xl"
            >
              再来一次
            </Button>
          </div>
        ) : (
          <div className="flex gap-3 items-end">
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isWaiting
                  ? '输入你的回答… (Enter 发送，Shift+Enter 换行)'
                  : 'AI 正在评估你的回答…'
              }
              disabled={!isWaiting}
              autoSize={{ minRows: 1, maxRows: 4 }}
              className="rounded-xl flex-1"
            />
            {isBusy ? (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={cancelStream}
                className="rounded-xl"
              >
                停止
              </Button>
            ) : (
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                loading={sending}
                disabled={!inputValue.trim() || !isWaiting}
                className="rounded-xl"
              >
                发送
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
