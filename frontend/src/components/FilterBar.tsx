// ============================================================
// FilterBar — 搜索 + 难度/公司/标签筛选（搜索框 300ms 防抖）
// ============================================================

import { useRef, useCallback, useEffect } from 'react'
import { Input, Select, Space } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { useAppStore } from '../store'

const { Option } = Select

const DIFFICULTY_LABELS: Record<string, string> = {
  easy: '🟢 初级',
  medium: '🟡 中级',
  hard: '🔴 高级',
}

const DEBOUNCE_MS = 300

export default function FilterBar() {
  const { filters, setFilters, filterOptions, applyFilters } = useAppStore()
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // 组件卸载时清理定时器
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  const handleSelectChange = (key: string, value: string | undefined) => {
    // 取消搜索防抖定时器，避免覆盖本次筛选
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
      debounceRef.current = null
    }
    setFilters({ [key]: value || '' })
    // 下拉选择即时触发
    applyFilters()
  }

  const handleSearchChange = useCallback((value: string) => {
    setFilters({ search: value })
    // 搜索输入防抖 300ms
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      applyFilters()
    }, DEBOUNCE_MS)
  }, [])

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 mb-6">
      <Space wrap size="middle" className="w-full">
        <Input
          placeholder="搜索题目关键词…"
          prefix={<SearchOutlined className="text-gray-400" />}
          value={filters.search}
          onChange={(e) => handleSearchChange(e.target.value)}
          allowClear
          onClear={() => handleSelectChange('search', '')}
          style={{ width: 280 }}
        />

        <Select
          placeholder="难度筛选"
          value={filters.difficulty || undefined}
          onChange={(v) => handleSelectChange('difficulty', v === 'all' ? '' : v)}
          style={{ width: 140 }}
        >
          <Option value="all">🔘 不限</Option>
          {filterOptions.difficulties.map((d) => (
            <Option key={d} value={d}>{DIFFICULTY_LABELS[d] || d}</Option>
          ))}
        </Select>

        <Select
          placeholder="公司筛选"
          value={filters.company || undefined}
          onChange={(v) => handleSelectChange('company', v === 'all' ? '' : v)}
          style={{ width: 140 }}
        >
          <Option value="all">🔘 不限</Option>
          {filterOptions.companies.map((c) => (
            <Option key={c} value={c}>{c}</Option>
          ))}
        </Select>

        <Select
          placeholder="标签筛选"
          value={filters.category || undefined}
          onChange={(v) => handleSelectChange('category', v === 'all' ? '' : v)}
          style={{ width: 160 }}
        >
          <Option value="all">🔘 不限</Option>
          {filterOptions.categories.map((c) => (
            <Option key={c} value={c}>{c}</Option>
          ))}
        </Select>
      </Space>
    </div>
  )
}
