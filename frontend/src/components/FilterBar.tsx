// ============================================================
// FilterBar — 搜索 + 难度/公司/标签筛选
// ============================================================

import { Input, Select, Space } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { useAppStore } from '../store'

const { Option } = Select

const DIFFICULTY_LABELS: Record<string, string> = {
  easy: '🟢 初级',
  medium: '🟡 中级',
  hard: '🔴 高级',
}

export default function FilterBar() {
  const { filters, setFilters, filterOptions, applyFilters } = useAppStore()

  const handleChange = (key: string, value: string | undefined) => {
    setFilters({ [key]: value || '' })
    applyFilters()
  }

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 mb-6">
      <Space wrap size="middle" className="w-full">
        <Input
          placeholder="搜索题目关键词…"
          prefix={<SearchOutlined className="text-gray-400" />}
          value={filters.search}
          onChange={(e) => handleChange('search', e.target.value)}
          allowClear
          onClear={() => handleChange('search', '')}
          style={{ width: 280 }}
        />

        <Select
          placeholder="难度筛选"
          value={filters.difficulty || undefined}
          onChange={(v) => handleChange('difficulty', v === 'all' ? '' : v)}
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
          onChange={(v) => handleChange('company', v === 'all' ? '' : v)}
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
          onChange={(v) => handleChange('category', v === 'all' ? '' : v)}
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
