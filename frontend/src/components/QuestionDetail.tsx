// ============================================================
// QuestionDetailPage — 提示与答案独立展开/收起
// 管理员可编辑和删除题目
// ============================================================

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Tag, Divider, Card, Alert, Empty, Collapse } from 'antd'
import {
  BulbOutlined,
  EyeOutlined,
  LinkOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  GithubOutlined,
  CaretRightOutlined,
  CheckCircleOutlined,
  CheckCircleFilled,
  StarOutlined,
  StarFilled,
  ShakeOutlined,
} from '@ant-design/icons'
import { Tooltip } from 'antd'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useAppStore } from '../store'
import type { QuestionDetail as QD, QuestionState } from '../types'

const DIFFICULTY_MAP: Record<string, { label: string; color: string }> = {
  easy: { label: '初级', color: 'green' },
  medium: { label: '中级', color: 'orange' },
  hard: { label: '高级', color: 'red' },
}

export default function QuestionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const {
    currentQuestion,
    revealHint,
    revealAnswer,
    fetchQuestionDetail,
    toggleHint,
    toggleAnswer,
    questionStates,
    setQuestionState,
    filteredQuestions,
    fetchQuestions,
  } = useAppStore()

  // 计算上一题/下一题 ID（基于筛选后的列表）
  const currentIndex = filteredQuestions.findIndex((q) => q.id === Number(id))
  const totalFiltered = filteredQuestions.length
  const prevId = currentIndex > 0 ? filteredQuestions[currentIndex - 1].id : null
  const nextId = currentIndex < totalFiltered - 1 ? filteredQuestions[currentIndex + 1].id : null

  const navigateToQuestion = (qid: number) => {
    navigate(`/question/${qid}`)
    fetchQuestionDetail(qid)
  }

  const goToRandom = () => {
    if (filteredQuestions.length === 0) return
    const currentIdx = filteredQuestions.findIndex((q) => q.id === Number(id))
    let randomIdx: number
    do {
      randomIdx = Math.floor(Math.random() * filteredQuestions.length)
    } while (filteredQuestions.length > 1 && randomIdx === currentIdx)
    navigateToQuestion(filteredQuestions[randomIdx].id)
  }

  // 键盘快捷键：← → 翻题
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 不拦截输入框内的按键
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.key === 'ArrowLeft' && prevId != null) {
        e.preventDefault()
        navigateToQuestion(prevId)
      } else if (e.key === 'ArrowRight' && nextId != null) {
        e.preventDefault()
        navigateToQuestion(nextId)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [prevId, nextId])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)
    // 并行加载详请和列表，确保上下题按钮有数据
    Promise.all([
      fetchQuestionDetail(Number(id)),
      filteredQuestions.length === 0 ? fetchQuestions() : Promise.resolve(),
    ])
      .catch((e: any) => setError(e.message || 'Question not found'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto pb-20">
        {/* 顶部导航骨架 */}
        <div className="flex items-center justify-between mb-6">
          <div className="h-5 w-20 bg-gray-100 rounded animate-pulse" />
          <div className="h-4 w-12 bg-gray-100 rounded animate-pulse" />
        </div>
        {/* 标题卡片骨架 */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6 border border-gray-100">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-6 w-12 bg-gray-100 rounded animate-pulse" />
            <div className="h-6 w-16 bg-gray-100 rounded animate-pulse" />
            <div className="h-6 w-20 bg-gray-100 rounded animate-pulse" />
          </div>
          <div className="h-7 bg-gray-100 rounded animate-pulse w-2/3 mb-4" />
          <div className="h-7 bg-gray-100 rounded animate-pulse w-1/2" />
        </div>
        {/* 折叠面板骨架 */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-5 h-5 rounded bg-gray-100 animate-pulse" />
            <div className="h-5 bg-gray-100 rounded animate-pulse w-24" />
          </div>
          <div className="h-4 bg-gray-50 rounded animate-pulse w-full mb-2" />
          <div className="h-4 bg-gray-50 rounded animate-pulse w-3/4" />
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-5 h-5 rounded bg-gray-100 animate-pulse" />
            <div className="h-5 bg-gray-100 rounded animate-pulse w-24" />
          </div>
          <div className="h-4 bg-gray-50 rounded animate-pulse w-full mb-2" />
          <div className="h-4 bg-gray-50 rounded animate-pulse w-5/6 mb-2" />
          <div className="h-4 bg-gray-50 rounded animate-pulse w-2/3" />
        </div>
      </div>
    )
  }

  if (error || !currentQuestion) {
    return (
      <div className="max-w-3xl mx-auto py-20">
        <Alert
          type={error?.includes('deleted') ? 'warning' : 'error'}
          message="Question not available"
          description={error || 'This question may have been deleted. Please return to the homepage.'}
          showIcon
          action={
            <Button type="primary" onClick={() => navigate('/')}>Return Home</Button>
          }
        />
      </div>
    )
  }

  const q: QD = currentQuestion
  const diff = DIFFICULTY_MAP[q.difficulty]
  const currentState: QuestionState | undefined = questionStates[q.id]

  const handleStateToggle = (state: QuestionState) => {
    if (currentState === state) {
      setQuestionState(q.id, null)
    } else {
      setQuestionState(q.id, state)
    }
  }

  const collapseItems = [
    {
      key: 'hint',
      label: (
        <span className="flex items-center gap-2 text-base font-medium">
          <BulbOutlined style={{ color: '#faad14' }} />
          解题提示
        </span>
      ),
      children: <p className="text-gray-700 leading-relaxed">{q.hint}</p>,
    },
    {
      key: 'answer',
      label: (
        <span className="flex items-center gap-2 text-base font-medium">
          <EyeOutlined style={{ color: '#1677ff' }} />
          标准答案
        </span>
      ),
      children: (
        <div className="answer-content prose max-w-none">
          <ReactMarkdown
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '')
                const codeStr = String(children).replace(/\n$/, '')
                if (!match) {
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  )
                }
                return (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={match[1]}
                    PreTag="pre"
                    customStyle={{
                      borderRadius: 8,
                      fontSize: 14,
                      padding: '16px 20px',
                    }}
                  >
                    {codeStr}
                  </SyntaxHighlighter>
                )
              },
            }}
          >
            {q.answer}
          </ReactMarkdown>
        </div>
      ),
    },
  ]

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* ─── 返回 + 上下翻题 ────────────────── */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-1 text-gray-500 hover:text-blue-500
                     transition-colors bg-transparent border-0 cursor-pointer"
        >
          <ArrowLeftOutlined /> 返回题库
        </button>

        <span className="text-xs text-gray-400">
          {currentIndex >= 0 ? currentIndex + 1 : '?'} / {totalFiltered}
        </span>

        <button
          onClick={goToRandom}
          title="随机一题"
          className="flex items-center gap-1 text-sm text-gray-400 hover:text-[#1677ff] transition-colors bg-transparent border-0 cursor-pointer"
        >
          <ShakeOutlined /> 随机
        </button>
      </div>

      {/* ─── 题目头部 ───────────────────────── */}
      <Card className="mb-6 rounded-xl shadow-sm">
        <div className="flex items-center gap-3 flex-wrap mb-3">
          <Tag color={diff.color} className="text-sm px-3 py-0.5">
            {diff.label}
          </Tag>
          {q.company && (
            <Tag className="text-sm px-3 py-0.5">{q.company}</Tag>
          )}
          <Tag className="text-sm px-3 py-0.5">{q.category}</Tag>
          {/* State buttons */}
          <Tooltip title={currentState === 'mastered' ? '取消已学会' : '标记已学会'}>
            <button
              className={`flex items-center gap-0.5 text-xs cursor-pointer border-0 rounded-full px-2 py-1 font-medium transition-colors
                ${currentState === 'mastered' ? 'bg-green-50 text-green-500' : 'bg-gray-50 text-gray-400 hover:text-green-500 hover:bg-green-50'}`}
              onClick={() => handleStateToggle('mastered')}
            >
              {currentState === 'mastered' ? <CheckCircleFilled /> : <CheckCircleOutlined />}
            </button>
          </Tooltip>
          <Tooltip title={currentState === 'bookmarked' ? '取消收藏' : '收藏'}>
            <button
              className={`flex items-center gap-0.5 text-xs cursor-pointer border-0 rounded-full px-2 py-1 font-medium transition-colors
                ${currentState === 'bookmarked' ? 'bg-amber-50 text-amber-500' : 'bg-gray-50 text-gray-400 hover:text-amber-500 hover:bg-amber-50'}`}
              onClick={() => handleStateToggle('bookmarked')}
            >
              {currentState === 'bookmarked' ? <StarFilled /> : <StarOutlined />}
            </button>
          </Tooltip>
        </div>
        <h1 className="text-xl md:text-2xl font-semibold text-gray-900 leading-relaxed mb-4">
          {q.title}
        </h1>
        {/* 预期关键词 — 帮用户了解评分维度 */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-gray-400 mr-1">考察点：</span>
          {(Array.isArray(q.expected_keywords) ? q.expected_keywords : []).map((kw: string) => (
            <Tag key={kw} className="text-xs bg-blue-50 text-blue-600 border-blue-100">
              {kw}
            </Tag>
          ))}
        </div>
      </Card>

      {/* ─── 提示 & 答案 — 并列折叠面板 ──────── */}
      <Collapse
        activeKey={[
          ...(revealHint ? ['hint'] : []),
          ...(revealAnswer ? ['answer'] : []),
        ]}
        onChange={(keys) => {
          const keySet = new Set(Array.isArray(keys) ? keys : [keys])
          const hintNow = keySet.has('hint')
          const answerNow = keySet.has('answer')
          if (hintNow !== revealHint) toggleHint()
          if (answerNow !== revealAnswer) toggleAnswer()
        }}
        items={collapseItems}
        expandIcon={({ isActive }) => (
          <CaretRightOutlined rotate={isActive ? 90 : 0} />
        )}
        size="large"
        className="bg-white rounded-xl shadow-sm [&_.ant-collapse-header]:!items-center"
        style={{ border: '1px solid #f0f0f0' }}
      />

      {/* ─── 代码引用（答案展开后显示） ──────── */}
      {revealAnswer && q.references.length > 0 && (
        <>
          <Divider
            className="!text-gray-400 !text-sm"
            style={{ borderColor: '#e5e7eb', marginTop: 24, marginBottom: 16 }}
          >
            📚 来自知识库的相关文档
          </Divider>
          <p className="text-xs text-gray-400 mb-4 leading-relaxed">
            以下引用仅提供 GitHub 文件链接跳转，方便快速查阅相关文档片段，不复制或分发任何仓库内容。如涉及侵权请联系删除。
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {q.references.map((ref) => (
              <Card
                key={ref.id}
                size="small"
                className="rounded-xl shadow-sm hover:shadow-md transition-shadow"
                title={
                  <a
                    href={ref.repoUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-sm text-blue-600
                               hover:text-blue-800"
                  >
                    <GithubOutlined /> {ref.repoName}
                  </a>
                }
              >
                <div className="text-xs text-gray-400 mb-2">
                  {ref.filePath} ({ref.lineRange})
                </div>
                <p className="text-sm text-gray-600 mb-3">{ref.description}</p>

                {ref.codeSnippet && (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={
                      ref.filePath.endsWith('.py')
                        ? 'python'
                        : ref.filePath.endsWith('.ts') || ref.filePath.endsWith('.tsx')
                          ? 'typescript'
                          : 'markdown'
                    }
                    PreTag="pre"
                    customStyle={{
                      borderRadius: 8,
                      fontSize: 13,
                      padding: '12px 16px',
                    }}
                  >
                    {ref.codeSnippet}
                  </SyntaxHighlighter>
                )}

                <a
                  href={`${ref.repoUrl}/blob/main/${ref.filePath}#${ref.lineRange}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-blue-500
                             hover:text-blue-700 mt-2"
                >
                  <LinkOutlined /> 查看源文件 ({ref.lineRange})
                </a>
              </Card>
            ))}
          </div>
        </>
      )}

      {revealAnswer && q.references.length === 0 && (
        <Empty description="No linked references" className="py-8" />
      )}

      {/* ─── 左右浮动导航 ────────────────── */}
      <button
        onClick={() => prevId && navigateToQuestion(prevId)}
        disabled={!prevId}
        title={prevId ? '上一题' : '已是第一题'}
        className={`fixed left-0 top-1/2 -translate-y-1/2 z-40
          hidden sm:flex items-center gap-2 pl-3 pr-5 py-3
          bg-[#1677ff] shadow-lg shadow-blue-500/30
          rounded-r-2xl transition-all duration-300 cursor-pointer border-0
          ${prevId
            ? 'text-white hover:bg-[#4096ff] hover:shadow-xl hover:shadow-blue-400/40 hover:pl-4 hover:pr-6'
            : 'opacity-0 pointer-events-none'
          }`}
      >
        <ArrowLeftOutlined className="text-lg" />
        <span className="text-sm font-semibold tracking-wide">上一题</span>
      </button>

      <button
        onClick={() => nextId && navigateToQuestion(nextId)}
        disabled={!nextId}
        title={nextId ? '下一题' : '已是最后一题'}
        className={`fixed right-0 top-1/2 -translate-y-1/2 z-40
          hidden sm:flex items-center gap-2 pl-5 pr-3 py-3
          bg-[#1677ff] shadow-lg shadow-blue-500/30
          rounded-l-2xl transition-all duration-300 cursor-pointer border-0
          ${nextId
            ? 'text-white hover:bg-[#4096ff] hover:shadow-xl hover:shadow-blue-400/40 hover:pl-6 hover:pr-4'
            : 'opacity-0 pointer-events-none'
          }`}
      >
        <span className="text-sm font-semibold tracking-wide">下一题</span>
        <ArrowRightOutlined className="text-lg" />
      </button>

      {/* ─── 移动端底部导航栏 ────────────────── */}
      <div className="sm:hidden fixed bottom-0 left-0 right-0 z-40
        flex items-center justify-between px-4 py-3
        bg-white/95 backdrop-blur-sm border-t border-gray-200 shadow-[0_-4px_12px_rgba(0,0,0,0.06)]">
        <button
          onClick={() => prevId && navigateToQuestion(prevId)}
          disabled={!prevId}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-colors border-0 cursor-pointer
            ${prevId
              ? 'bg-gray-50 text-gray-700 active:bg-blue-50 active:text-[#1677ff]'
              : 'text-gray-300 cursor-not-allowed bg-transparent opacity-50'
            }`}
        >
          <ArrowLeftOutlined /> 上一题
        </button>
        <button
          onClick={goToRandom}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium
            bg-[#1677ff]/10 text-[#1677ff] active:bg-[#1677ff]/20 transition-colors border-0 cursor-pointer"
        >
          <ShakeOutlined /> 随机
        </button>
        <button
          onClick={() => nextId && navigateToQuestion(nextId)}
          disabled={!nextId}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-colors border-0 cursor-pointer
            ${nextId
              ? 'bg-gray-50 text-gray-700 active:bg-blue-50 active:text-[#1677ff]'
              : 'text-gray-300 cursor-not-allowed bg-transparent opacity-50'
            }`}
        >
          下一题 <ArrowRightOutlined />
        </button>
      </div>
    </div>
  )
}
