// ============================================================
// AI 面试通 — Zustand Store（对接真实后端 API）
// ============================================================

import { create } from 'zustand'
import type { Question, QuestionDetail, Filters, FilterOptions, Pagination } from '../types'

const API_BASE = '/api'

interface AppStore {
  // ─── 筛选状态 ─────────────────────────────
  filters: Filters
  setFilters: (f: Partial<Filters>) => void
  filterOptions: FilterOptions

  // ─── 题目列表 ─────────────────────────────
  questions: Question[]
  filteredQuestions: Question[]
  pagination: Pagination
  loading: boolean
  fetchQuestions: () => Promise<void>
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

const PAGE_SIZE = 12

export const useAppStore = create<AppStore>((set, get) => ({
  // ─── 筛选状态 ─────────────────────────────
  filters: { difficulty: '', company: '', search: '', category: '' },
  setFilters: (f) => {
    set((s) => ({ filters: { ...s.filters, ...f } }))
  },
  filterOptions: { difficulties: [], companies: [], categories: [] },

  // ─── 题目列表 ─────────────────────────────
  questions: [],
  filteredQuestions: [],
  pagination: { page: 1, pageSize: PAGE_SIZE, total: 0 },
  loading: false,

  fetchQuestions: async () => {
    set({ loading: true })
    try {
      const { filters } = get()
      const params = new URLSearchParams()
      if (filters.difficulty) params.set('difficulty', filters.difficulty)
      if (filters.company) params.set('company', filters.company)
      if (filters.category) params.set('category', filters.category)
      if (filters.search) params.set('search', filters.search)
      params.set('page', '1')
      params.set('page_size', '50') // 分批加载，减少首屏等待

      const res = await fetch(`${API_BASE}/questions?${params}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      const questions: Question[] = data.questions.map((q: any) => ({
        id: q.id,
        title: q.title,
        difficulty: q.difficulty,
        company: q.company,
        category: q.category,
        hint: q.hint,
        answer: q.answer,
        source: q.source,
        sourceUrl: q.source_url,
        createdAt: q.created_at,
      }))

      set({
        questions,
        filteredQuestions: questions,
        pagination: { page: 1, pageSize: PAGE_SIZE, total: questions.length },
      })
    } catch (e: any) {
      console.error('fetchQuestions failed:', e)
      set({ questions: [], filteredQuestions: [] })
    } finally {
      set({ loading: false })
    }
  },

  applyFilters: async () => {
    const { filters, questions } = get()
    let result = [...questions]

    if (filters.difficulty)
      result = result.filter((q) => q.difficulty === filters.difficulty)
    if (filters.company)
      result = result.filter((q) => q.company === filters.company)
    if (filters.category)
      result = result.filter((q) => q.category === filters.category)
    if (filters.search) {
      const s = filters.search.toLowerCase()
      result = result.filter(
        (q) =>
          q.title.toLowerCase().includes(s) ||
          (q.answer && q.answer.toLowerCase().includes(s)),
      )
    }

    set({
      filteredQuestions: result,
      pagination: { page: 1, pageSize: PAGE_SIZE, total: result.length },
    })
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
      set((s) => ({
        questions: s.questions.filter((q) => q.id !== id),
        filteredQuestions: s.filteredQuestions.filter((q) => q.id !== id),
      }))
      return true
    } catch (e: any) {
      console.error('deleteQuestion failed:', e)
      throw e
    }
  },
}))
