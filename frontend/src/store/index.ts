// ============================================================
// 面试通 — Zustand Store（对接真实后端 API）
// ============================================================

import { create } from 'zustand'
import type { Question, QuestionDetail, QuestionState, Filters, FilterOptions, Pagination } from '../types'

const API_BASE = '/api'
const LS_KEY = 'question_states'

// ─── 辅助：按用户状态过滤题目 ──────────────────
function applyStateFilter(questions: Question[], stateFilter: string, states: Record<number, QuestionState>): Question[] {
  if (!stateFilter || stateFilter === '') {
    // 默认：排除已学会的题，保留收藏和未标记的题
    return questions.filter(q => states[q.id] !== 'mastered')
  }
  if (stateFilter === 'all') return questions
  if (stateFilter === 'mastered') return questions.filter(q => states[q.id] === 'mastered')
  if (stateFilter === 'bookmarked') return questions.filter(q => states[q.id] === 'bookmarked')
  return questions
}

interface AppStore {
  // ─── 筛选状态 ─────────────────────────────
  filters: Filters
  setFilters: (f: Partial<Filters>) => void
  filterOptions: FilterOptions

  // ─── 题目状态（localStorage） ─────────────
  questionStates: Record<number, QuestionState>
  loadQuestionStates: () => void
  setQuestionState: (id: number, state: QuestionState | null) => void

  // ─── 题目列表（无限滚动） ─────────────────
  questions: Question[]
  filteredQuestions: Question[]
  pagination: Pagination
  loading: boolean
  hasMore: boolean
  fetchQuestions: (reset?: boolean) => Promise<void>
  loadMore: () => Promise<void>
  applyFilters: () => Promise<void>
  setPage: (page: number) => void

  // ─── 题目详情 ─────────────────────────────
  currentQuestion: QuestionDetail | null
  revealHint: boolean
  revealAnswer: boolean
  fetchQuestionDetail: (id: number) => Promise<void>
  toggleHint: () => void
  toggleAnswer: () => void

  // ─── 管理页面 ─────────────────────────────
  stats: Record<string, any> | null
  crawlStatus: 'idle' | 'running' | 'done' | 'error'
  adminToken: string
  setAdminToken: (t: string) => void
  fetchFilterOptions: () => Promise<void>
  fetchStats: () => Promise<void>
  triggerCrawl: (maxPages?: number) => Promise<void>
  updateQuestion: (id: number, data: Partial<Question>) => Promise<QuestionDetail | null>
  deleteQuestion: (id: number) => Promise<boolean>
}

const FETCH_SIZE = 50  // 每次从后端拉取的题目数

export const useAppStore = create<AppStore>((set, get) => ({
  // ─── 筛选状态 ─────────────────────────────
  filters: { difficulty: '', company: '', search: '', category: '', state: '' },
  setFilters: (f) => {
    set((s) => ({ filters: { ...s.filters, ...f } }))
  },
  filterOptions: { difficulties: [], companies: [], categories: [] },

  // ─── 题目状态（localStorage） ─────────────
  questionStates: {},

  loadQuestionStates: () => {
    try {
      const raw = localStorage.getItem(LS_KEY)
      if (raw) set({ questionStates: JSON.parse(raw) })
    } catch { /* corrupted data, reset */ }
  },

  setQuestionState: (id, state) => {
    set((s) => {
      const next = { ...s.questionStates }
      if (state === null) {
        delete next[id]
      } else {
        next[id] = state
      }
      localStorage.setItem(LS_KEY, JSON.stringify(next))

      // 立即重新过滤列表，让卡片状态即时反映
      const filtered = applyStateFilter(s.questions, s.filters.state, next)

      return { questionStates: next, filteredQuestions: filtered }
    })
  },

  // ─── 题目列表（无限滚动） ─────────────────
  questions: [],
  filteredQuestions: [],
  pagination: { page: 1, pageSize: FETCH_SIZE, total: 0 },
  loading: false,
  hasMore: true,

  fetchQuestions: async (_reset = true) => {
    set({ loading: true })
    try {
      const { filters } = get()
      const params = new URLSearchParams()
      if (filters.difficulty) params.set('difficulty', filters.difficulty)
      if (filters.company) params.set('company', filters.company)
      if (filters.category) params.set('category', filters.category)
      if (filters.search) params.set('search', filters.search)
      params.set('page', '1')
      params.set('page_size', String(FETCH_SIZE))

      const res = await fetch(`${API_BASE}/questions?${params}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      const questions: Question[] = data.questions.map((q: any) => ({
        id: q.id, title: q.title, difficulty: q.difficulty,
        company: q.company, category: q.category, hint: q.hint,
        answer: q.answer, expected_keywords: q.expected_keywords || [],
        source: q.source, sourceUrl: q.source_url,
        createdAt: q.created_at,
      }))

      const filtered = applyStateFilter(questions, filters.state, get().questionStates)

      set({
        questions,
        filteredQuestions: filtered,
        pagination: { page: 1, pageSize: FETCH_SIZE, total: data.total },
        hasMore: questions.length < data.total,
      })
    } catch (e: any) {
      console.error('fetchQuestions failed:', e)
      set({ questions: [], filteredQuestions: [], hasMore: false })
    } finally {
      set({ loading: false })
    }
  },

  loadMore: async () => {
    const { hasMore, loading, pagination, questions, filters } = get()
    if (!hasMore || loading) return

    const nextPage = Math.floor(questions.length / FETCH_SIZE) + 1
    set({ loading: true })

    try {
      const params = new URLSearchParams()
      if (filters.difficulty) params.set('difficulty', filters.difficulty)
      if (filters.company) params.set('company', filters.company)
      if (filters.category) params.set('category', filters.category)
      if (filters.search) params.set('search', filters.search)
      params.set('page', String(nextPage))
      params.set('page_size', String(FETCH_SIZE))

      const res = await fetch(`${API_BASE}/questions?${params}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      const newQuestions: Question[] = data.questions.map((q: any) => ({
        id: q.id, title: q.title, difficulty: q.difficulty,
        company: q.company, category: q.category, hint: q.hint,
        answer: q.answer, source: q.source, sourceUrl: q.source_url,
        createdAt: q.created_at,
      }))

      const merged = [...questions, ...newQuestions]
      const filtered = applyStateFilter(merged, filters.state, get().questionStates)
      set({
        questions: merged,
        filteredQuestions: filtered,
        pagination: { ...pagination, page: nextPage, total: data.total },
        hasMore: merged.length < data.total,
      })
    } catch (e: any) {
      console.error('loadMore failed:', e)
    } finally {
      set({ loading: false })
    }
  },

  applyFilters: async () => {
    // 筛选条件变化时重新从后端首页拉取
    const { filters } = get()
    set({ loading: true })
    try {
      const params = new URLSearchParams()
      if (filters.difficulty) params.set('difficulty', filters.difficulty)
      if (filters.company) params.set('company', filters.company)
      if (filters.category) params.set('category', filters.category)
      if (filters.search) params.set('search', filters.search)
      params.set('page', '1')
      params.set('page_size', String(FETCH_SIZE))

      const res = await fetch(`${API_BASE}/questions?${params}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      const questions: Question[] = data.questions.map((q: any) => ({
        id: q.id, title: q.title, difficulty: q.difficulty,
        company: q.company, category: q.category, hint: q.hint,
        answer: q.answer, expected_keywords: q.expected_keywords || [],
        source: q.source, sourceUrl: q.source_url,
        createdAt: q.created_at,
      }))

      const filtered = applyStateFilter(questions, filters.state, get().questionStates)

      set({
        questions,
        filteredQuestions: filtered,
        pagination: { page: 1, pageSize: FETCH_SIZE, total: data.total },
        hasMore: questions.length < data.total,
      })
    } catch (e: any) {
      console.error('applyFilters failed:', e)
      set({ questions: [], filteredQuestions: [], hasMore: false })
    } finally {
      set({ loading: false })
    }
  },

  setPage: (page) => {
    set((s) => ({ pagination: { ...s.pagination, page } }))
  },

  // ─── 题目详情 ─────────────────────────────
  currentQuestion: null,
  revealHint: false,
  revealAnswer: false,

  fetchQuestionDetail: async (id: number) => {
    set({ currentQuestion: null, revealHint: false, revealAnswer: false })
    try {
      const res = await fetch(`${API_BASE}/questions/${id}`)
      if (!res.ok) {
        if (res.status === 404) throw new Error('This question may have been deleted')
        throw new Error(`HTTP ${res.status}`)
      }
      const q: any = await res.json()

      const detail: QuestionDetail = {
        id: q.id,
        title: q.title,
        difficulty: q.difficulty,
        company: q.company,
        category: q.category,
        hint: q.hint,
        answer: q.answer,
        expected_keywords: q.expected_keywords || [],
        source: q.source,
        sourceUrl: q.source_url,
        createdAt: q.created_at,
        references: (q.references || []).map((ref: any) => ({
          id: ref.id,
          questionId: ref.question_id,
          repoName: ref.repo_name,
          repoUrl: ref.repo_url,
          filePath: ref.file_path,
          lineRange: ref.line_range,
          codeSnippet: ref.code_snippet,
          description: ref.description,
        })),
      }
      set({ currentQuestion: detail })
    } catch (e: any) {
      console.error('fetchQuestionDetail failed:', e)
      set({ currentQuestion: null })
    }
  },

  toggleHint: () => set((s) => ({ revealHint: !s.revealHint })),
  toggleAnswer: () => set((s) => ({ revealAnswer: !s.revealAnswer })),

  // ─── 管理页面 ─────────────────────────────
  stats: null,
  crawlStatus: 'idle',
  adminToken: localStorage.getItem('admin_token') || '',

  setAdminToken: (t) => {
    localStorage.setItem('admin_token', t)
    set({ adminToken: t })
  },

  fetchFilterOptions: async () => {
    try {
      const res = await fetch(`${API_BASE}/filters`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      set({
        filterOptions: {
          difficulties: data.difficulties || [],
          companies: data.companies || [],
          categories: data.categories || [],
        },
      })
    } catch (e: any) {
      console.error('fetchFilterOptions failed:', e)
    }
  },

  fetchStats: async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      set({ stats: data })
    } catch (e: any) {
      console.error('fetchStats failed:', e)
    }
  },

  triggerCrawl: async (maxPages = 5) => {
    set({ crawlStatus: 'running' })
    try {
      const res = await fetch(`${API_BASE}/admin/crawl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_pages: maxPages }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      set({ crawlStatus: 'done' })
      return data
    } catch (e: any) {
      console.error('triggerCrawl failed:', e)
      set({ crawlStatus: 'error' })
      throw e
    }
  },

  updateQuestion: async (id, data) => {
    try {
      const res = await fetch(`${API_BASE}/admin/questions/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const q = await res.json()
      const detail: QuestionDetail = {
        id: q.id, title: q.title, difficulty: q.difficulty,
        company: q.company, category: q.category, hint: q.hint,
        answer: q.answer, source: q.source, sourceUrl: q.source_url,
        createdAt: q.created_at,
        references: (q.references || []).map((ref: any) => ({
          id: ref.id, questionId: ref.question_id,
          repoName: ref.repo_name, repoUrl: ref.repo_url,
          filePath: ref.file_path, lineRange: ref.line_range,
          codeSnippet: ref.code_snippet, description: ref.description,
        })),
      }
      set({ currentQuestion: detail })
      return detail
    } catch (e: any) {
      console.error('updateQuestion failed:', e)
      throw e
    }
  },

  deleteQuestion: async (id) => {
    try {
      const res = await fetch(`${API_BASE}/admin/questions/${id}`, {
        method: 'DELETE',
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      // 立即从本地状态中移除已删题目，无需等待重新 fetch
      set((s) => {
        const questions = s.questions.filter((q) => q.id !== id)
        const filtered = applyStateFilter(questions, s.filters.state, s.questionStates)
        return { questions, filteredQuestions: filtered }
      })
      return true
    } catch (e: any) {
      console.error('deleteQuestion failed:', e)
      throw e
    }
  },
}))
