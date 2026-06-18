// ============================================================
// 面试通 — TypeScript 类型定义
// ============================================================

/** 难度等级 */
export type Difficulty = 'easy' | 'medium' | 'hard'

/** 题目标签（可扩展，后续新增方向直接追加） */
export type QuestionCategory = string

/** 面试题 */
export interface Question {
  id: number
  title: string
  difficulty: Difficulty
  company: string | null
  category: QuestionCategory
  hint: string
  answer: string // Markdown
  source: 'local' | 'nowcoder' | 'hub'
  sourceUrl: string | null
  createdAt: string
}

/** 代码引用（关联知识库文档片段） */
export interface CodeReference {
  id: number
  questionId: number
  repoName: string
  repoUrl: string
  filePath: string
  lineRange: string
  codeSnippet: string
  description: string
}

/** 题目详情 = 题目 + 代码引用 */
export interface QuestionDetail extends Question {
  references: CodeReference[]
}

/** 题目状态（localStorage 持久化） */
export type QuestionState = 'mastered' | 'bookmarked'

/** 筛选条件 */
export interface Filters {
  difficulty: string
  company: string
  search: string
  category: string
  state: string
}

/** 筛选选项 */
export interface FilterOptions {
  difficulties: string[]
  companies: string[]
  categories: string[]
}

/** 分页参数 */
export interface Pagination {
  page: number
  pageSize: number
  total: number
}

// ─── 模块三：模拟面试 ──────────────────────────────

/** 聊天消息 */
export interface ChatMessage {
  id: string
  role: 'interviewer' | 'candidate' | 'system'
  content: string
  timestamp: number
  streaming?: boolean
}

/** 面试评估结果 */
export interface InterviewEvaluation {
  score: number
  keywordsMatched: string[]
  missingKeywords: string[]
  coverage: number
}

/** 面试会话状态 */
export type InterviewStatus =
  | 'idle'
  | 'setup'
  | 'waiting_for_answer'
  | 'evaluating'
  | 'streaming_critique'
  | 'completed'

/** 面试会话 */
export interface InterviewSession {
  sessionId: string
  difficulty: Difficulty
  totalQuestions: number
  currentQuestionNumber: number
  messages: ChatMessage[]
  status: InterviewStatus
  evaluation: InterviewEvaluation | null
}

/** 开始面试参数 */
export interface StartInterviewParams {
  difficulty: Difficulty
  totalQuestions: number
}
