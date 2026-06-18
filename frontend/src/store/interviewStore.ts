// ============================================================
// Agent 面试通 — 模拟面试 Zustand Store
// ============================================================

import { create } from 'zustand'
import type {
  ChatMessage,
  InterviewEvaluation,
  InterviewSession,
  InterviewStatus,
  StartInterviewParams,
} from '../types'

const API_BASE = '/api'

interface InterviewStore {
  // ─── 状态 ─────────────────────────────
  session: InterviewSession | null
  abortController: AbortController | null
  streamingContent: string

  // ─── 动作 ─────────────────────────────
  startInterview: (params: StartInterviewParams) => Promise<void>
  submitAnswer: (answer: string) => Promise<void>
  cancelStream: () => void
  resetInterview: () => void
  appendToken: (token: string) => void
  commitStreamingMessage: () => void
  setEvaluation: (eval_: InterviewEvaluation) => void
  setStatus: (status: InterviewStatus) => void
}

function msgId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export const useInterviewStore = create<InterviewStore>((set, get) => ({
  // ─── 初始状态 ─────────────────────────
  session: null,
  abortController: null,
  streamingContent: '',

  // ─── 开始面试 ─────────────────────────
  startInterview: async (params) => {
    const res = await fetch(`${API_BASE}/interview/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        difficulty: params.difficulty,
        total_questions: params.totalQuestions,
      }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()

    const questionMsg: ChatMessage = {
      id: msgId(),
      role: 'interviewer',
      content: `**【第 ${data.question_number} 题】** (${data.question.difficulty}) ${data.question.title}`,
      timestamp: Date.now(),
    }

    const session: InterviewSession = {
      sessionId: data.session_id,
      difficulty: params.difficulty,
      totalQuestions: params.totalQuestions,
      currentQuestionNumber: data.question_number,
      messages: [questionMsg],
      status: 'waiting_for_answer',
      evaluation: null,
    }

    set({ session, streamingContent: '' })
  },

  // ─── 提交回答 → SSE 流式消费 ──────────
  submitAnswer: async (answer) => {
    const { session } = get()
    if (!session) return

    // 添加候选人消息
    const candidateMsg: ChatMessage = {
      id: msgId(),
      role: 'candidate',
      content: answer,
      timestamp: Date.now(),
    }
    set((s) => ({
      session: s.session
        ? {
            ...s.session,
            messages: [...s.session.messages, candidateMsg],
            status: 'evaluating' as InterviewStatus,
          }
        : null,
      streamingContent: '',
    }))

    const controller = new AbortController()
    set({ abortController: controller })

    try {
      const res = await fetch(`${API_BASE}/interview/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.sessionId,
          answer,
        }),
        signal: controller.signal,
      })

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        // 解析 SSE 帧
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          for (const line of part.split('\n')) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                const store = get()
                if (!store.session) return

                if (line.includes('event: evaluate') || part.includes('event: evaluate')) {
                  // handled below
                }

                if (data.step === 'evaluate' && data.evaluation) {
                  get().setEvaluation(data.evaluation)
                } else if (data.step === 'critique_stream' && data.token) {
                  get().appendToken(data.token)
                } else if (data.step === 'critique_stream' && data.token === undefined) {
                  // done token — commit
                  get().commitStreamingMessage()
                } else if (data.step === 'critique') {
                  // fallback: single critique event
                  if (data.critique) {
                    set((s) => ({
                      streamingContent: '',
                      session: s.session
                        ? {
                            ...s.session,
                            messages: [
                              ...s.session.messages,
                              {
                                id: msgId(),
                                role: 'interviewer' as const,
                                content: data.critique,
                                timestamp: Date.now(),
                              },
                            ],
                          }
                        : null,
                    }))
                  }
                } else if (data.step === 'question' && data.question) {
                  get().commitStreamingMessage()
                  const nextMsg: ChatMessage = {
                    id: msgId(),
                    role: 'interviewer',
                    content: `**【第 ${data.question_number} 题】** (${data.question.difficulty}) ${data.question.title}`,
                    timestamp: Date.now(),
                  }
                  set((s) => ({
                    session: s.session
                      ? {
                          ...s.session,
                          messages: [...s.session.messages, nextMsg],
                          currentQuestionNumber: data.question_number,
                          status: 'waiting_for_answer' as InterviewStatus,
                        }
                      : null,
                  }))
                }
              } catch {
                // skip malformed SSE chunks
              }
            }
          }

          // Also try parsing the whole part as event+data
          const eventMatch = part.match(/^event:\s*(\w+)$/m)
          const dataMatch = part.match(/^data:\s*(.+)$/m)
          if (eventMatch && dataMatch) {
            try {
              const data = JSON.parse(dataMatch[1])
              const eventType = eventMatch[1]

              if (eventType === 'evaluate' && data.evaluation) {
                get().setEvaluation(data.evaluation)
              }

              if (eventType === 'done') {
                get().commitStreamingMessage()
              }

              if (eventType === 'critique' && data.critique) {
                // Fallback single-event critique
                set((s) => ({
                  streamingContent: '',
                  session: s.session
                    ? {
                        ...s.session,
                        messages: [
                          ...s.session.messages,
                          {
                            id: msgId(),
                            role: 'interviewer' as const,
                            content: data.critique,
                            timestamp: Date.now(),
                          },
                        ],
                      }
                    : null,
                }))
              }

              if (eventType === 'question' && data.question) {
                get().commitStreamingMessage()
                const nextMsg: ChatMessage = {
                  id: msgId(),
                  role: 'interviewer',
                  content: `**【第 ${data.question_number} 题】** (${data.question.difficulty}) ${data.question.title}`,
                  timestamp: Date.now(),
                }
                set((s) => ({
                  session: s.session
                    ? {
                        ...s.session,
                        messages: [...s.session.messages, nextMsg],
                        currentQuestionNumber: data.question_number,
                        status: 'waiting_for_answer' as InterviewStatus,
                      }
                    : null,
                }))
              }

              if (eventType === 'error') {
                console.error('Interview error:', data.message)
                set((s) => ({
                  session: s.session
                    ? { ...s.session, status: 'waiting_for_answer' as InterviewStatus }
                    : null,
                }))
              }
            } catch {
              // skip
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        // 用户主动取消 — 提交已有的流式内容
        get().commitStreamingMessage()
      } else {
        console.error('submitAnswer stream error:', err)
        set((s) => ({
          session: s.session
            ? { ...s.session, status: 'waiting_for_answer' as InterviewStatus }
            : null,
        }))
      }
    } finally {
      set({ abortController: null })
    }
  },

  // ─── 取消流式输出 ─────────────────────
  cancelStream: () => {
    const { abortController } = get()
    if (abortController) {
      abortController.abort()
    }
  },

  // ─── 重置 ─────────────────────────────
  resetInterview: () => {
    const { abortController } = get()
    if (abortController) abortController.abort()
    set({
      session: null,
      abortController: null,
      streamingContent: '',
    })
  },

  // ─── 追加 token ───────────────────────
  appendToken: (token) => {
    set((s) => ({
      streamingContent: s.streamingContent + token,
      session: s.session
        ? { ...s.session, status: 'streaming_critique' as InterviewStatus }
        : null,
    }))
  },

  // ─── 提交流式消息 ─────────────────────
  commitStreamingMessage: () => {
    const { streamingContent, session } = get()
    if (!streamingContent.trim() || !session) {
      set({ streamingContent: '' })
      return
    }

    const msg: ChatMessage = {
      id: msgId(),
      role: 'interviewer',
      content: streamingContent,
      timestamp: Date.now(),
    }
    set({
      streamingContent: '',
      session: {
        ...session,
        messages: [...session.messages, msg],
      },
    })
  },

  // ─── 设置评估 ─────────────────────────
  setEvaluation: (eval_) => {
    set((s) => ({
      session: s.session ? { ...s.session, evaluation: eval_ } : null,
    }))
  },

  // ─── 设置状态 ─────────────────────────
  setStatus: (status) => {
    set((s) => ({
      session: s.session ? { ...s.session, status } : null,
    }))
  },
}))
