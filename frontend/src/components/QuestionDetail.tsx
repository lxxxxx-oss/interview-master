// ============================================================
// QuestionDetailPage — 提示与答案独立展开/收起
// 管理员可编辑和删除题目
// ============================================================

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Tag, Divider, Card, Spin, Alert, Empty, Collapse, Modal, Input, Select, Form, Popconfirm, message } from 'antd'
import {
  BulbOutlined,
  EyeOutlined,
  LinkOutlined,
  ArrowLeftOutlined,
  GithubOutlined,
  CaretRightOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useAppStore } from '../store'
import type { QuestionDetail as QD, Difficulty, QuestionCategory } from '../types'

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
    updateQuestion,
    deleteQuestion,
    toggleHint,
    toggleAnswer,
  } = useAppStore()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // ─── 编辑弹窗状态 ─────────────────────────
  const [editOpen, setEditOpen] = useState(false)
  const [editForm] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const isAdmin = true  // 当前直接放行，后续登录系统接入后改为实际校验

  // ─── 编辑/删除操作 ───────────────────────
  const handleEdit = () => {
    const q = currentQuestion
    if (!q) return
    editForm.setFieldsValue({
      title: q.title,
      difficulty: q.difficulty,
      company: q.company || '',
      category: q.category,
      hint: q.hint,
      answer: q.answer,
    })
    setEditOpen(true)
  }

  const handleEditSave = async () => {
    if (!currentQuestion) return
    setSaving(true)
    try {
      const values = await editForm.validateFields()
      await updateQuestion(currentQuestion.id, values)
      message.success('Updated successfully')
      setEditOpen(false)
    } catch (e: any) {
      if (e.message) message.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!currentQuestion) return
    const qid = currentQuestion.id
    try {
      navigate('/', { replace: true })
      await deleteQuestion(qid)
      message.success('Deleted')
    } catch (e: any) {
      message.error(e.message || 'Delete failed')
    }
  }

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)
    fetchQuestionDetail(Number(id))
      .catch((e: any) => setError(e.message || 'Question not found'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex justify-center py-40">
        <Spin size="large" tip="Loading…" />
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
      {/* ─── 返回按钮 ───────────────────────── */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-1 text-gray-500 hover:text-blue-500
                   transition-colors mb-6 bg-transparent border-0 cursor-pointer"
      >
        <ArrowLeftOutlined /> 返回题库
      </button>

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
          <span className="text-xs text-gray-400">
            {q.source === 'local' ? '📝 面经收录' : '🌐 牛客网'}
          </span>
          {/* ─── 管理操作按钮 ──────── */}
          <div className="ml-auto flex items-center gap-2">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={handleEdit}
              className="text-gray-400 hover:text-blue-500"
            >
              Edit
            </Button>
            <Popconfirm
              title="Delete this question?"
              description="This will also remove all linked code references."
              onConfirm={handleDelete}
              okText="Delete"
              okType="danger"
              cancelText="Cancel"
            >
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                className="text-gray-400 hover:text-red-500"
              >
                Delete
              </Button>
            </Popconfirm>
          </div>
        </div>
        <h1 className="text-xl md:text-2xl font-semibold text-gray-900 leading-relaxed">
          {q.title}
        </h1>
      </Card>

      {/* ─── 提示 & 答案 — 并列折叠面板 ──────── */}
      <Collapse
        activeKey={[
          ...(revealHint ? ['hint'] : []),
          ...(revealAnswer ? ['answer'] : []),
        ]}
        onChange={(keys) => {
          const keySet = new Set(Array.isArray(keys) ? keys : [keys])
          // 对比当前状态，只切换变化了的那个
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

      {/* ═══ Admin Modals ══════════════════════════════════════════════════════════ */}

      {/* Edit Question Modal */}
      <Modal
        title="Edit Question"
        open={editOpen}
        onOk={handleEditSave}
        onCancel={() => setEditOpen(false)}
        okText="Save"
        confirmLoading={saving}
        width={720}
        destroyOnClose
      >
        <Form form={editForm} layout="vertical" className="mt-4">
          <Form.Item name="title" label="Title" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <div className="grid grid-cols-3 gap-4">
            <Form.Item name="difficulty" label="Difficulty" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: 'easy', label: 'Easy' },
                  { value: 'medium', label: 'Medium' },
                  { value: 'hard', label: 'Hard' },
                ]}
              />
            </Form.Item>
            <Form.Item name="company" label="Company">
              <Input placeholder="e.g. ByteDance" />
            </Form.Item>
            <Form.Item name="category" label="Category" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: 'Agent基础', label: 'Agent基础' },
                  { value: 'RAG', label: 'RAG' },
                  { value: 'MCP协议', label: 'MCP协议' },
                  { value: 'Function Calling', label: 'Function Calling' },
                  { value: 'Prompt Engineering', label: 'Prompt Engineering' },
                  { value: '记忆机制', label: '记忆机制' },
                  { value: '向量检索', label: '向量检索' },
                  { value: '模型架构', label: '模型架构' },
                ]}
              />
            </Form.Item>
          </div>
          <Form.Item name="hint" label="Hint">
            <Input.TextArea rows={3} placeholder="解题提示…" />
          </Form.Item>
          <Form.Item name="answer" label="Answer (Markdown)" rules={[{ required: true }]}>
            <Input.TextArea rows={12} placeholder="Markdown 格式的标准答案…" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
