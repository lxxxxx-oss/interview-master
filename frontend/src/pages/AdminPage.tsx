// ============================================================
// AdminPage — 爬取管理 + 题库统计（对接真实后端 API）
// ============================================================

import { useEffect } from 'react'
import { Card, Button, Statistic, Tag, Space, message, Spin } from 'antd'
import {
  CloudDownloadOutlined,
  DatabaseOutlined,
  GithubOutlined,
} from '@ant-design/icons'
import { useAppStore } from '../store'

export default function AdminPage() {
  const { stats, crawlStatus, fetchStats, triggerCrawl } = useAppStore()

  useEffect(() => {
    fetchStats()
  }, [])

  const handleCrawl = async () => {
    try {
      const result: any = await triggerCrawl(5)
      message.success(
        `爬取完成！爬取 ${result?.pages_crawled ?? '?'} 页，新增 ${result?.new_items ?? 0} 道题目`,
      )
      // 刷新统计
      await fetchStats()
    } catch {
      message.error('爬取出错，请检查后端服务和 Playwright 环境')
    }
  }

  const s = stats || {}
  const byDifficulty = s.by_difficulty || {}
  const bySource = s.by_source || {}

  return (
    <div className="max-w-5xl mx-auto pb-20">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">
        ⚙️ 题库管理
      </h1>

      {/* ─── 统计卡片 ───────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card size="small" className="rounded-xl shadow-sm text-center">
          <Statistic
            title="总题目数"
            value={s.total ?? '-'}
            prefix={<DatabaseOutlined />}
          />
        </Card>
        <Card size="small" className="rounded-xl shadow-sm text-center">
          <Statistic title="🟢 初级" value={byDifficulty.easy ?? 0} />
        </Card>
        <Card size="small" className="rounded-xl shadow-sm text-center">
          <Statistic title="🟡 中级" value={byDifficulty.medium ?? 0} />
        </Card>
        <Card size="small" className="rounded-xl shadow-sm text-center">
          <Statistic title="🔴 高级" value={byDifficulty.hard ?? 0} />
        </Card>
      </div>

      {/* ─── 爬取面板 ───────────────────────── */}
      <Card
        className="rounded-xl shadow-sm mb-8"
        title={
          <span className="flex items-center gap-2">
            <CloudDownloadOutlined /> 牛客网爬取
          </span>
        }
      >
        <div className="flex items-center gap-4 flex-wrap">
          <Button
            type="primary"
            size="large"
            icon={<CloudDownloadOutlined />}
            loading={crawlStatus === 'running'}
            onClick={handleCrawl}
          >
            {crawlStatus === 'running' ? '爬取中…' : '开始爬取'}
          </Button>

          <span className="text-sm text-gray-500">
            {(bySource.nowcoder ?? 0) > 0
              ? `当前已收录 ${bySource.nowcoder} 道牛客面经`
              : '暂无牛客数据，点击开始首次爬取'}
          </span>
        </div>

        {s.last_crawl && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
            最近爬取：{s.last_crawl.pages_crawled} 页，新增 {s.last_crawl.new_items} 题，
            状态：{s.last_crawl.status}
            {s.last_crawl.created_at && ` (${s.last_crawl.created_at})`}
          </div>
        )}

        {crawlStatus === 'running' && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg text-sm text-gray-600">
            <Spin size="small" /> 正在使用 Playwright 模拟浏览器爬取牛客网…
            <br />
            <span className="text-xs text-gray-400">
              此过程约需 1-2 分钟，请耐心等待
            </span>
          </div>
        )}
      </Card>

      {/* ─── 来源统计 ───────────────────────── */}
      <Card
        className="rounded-xl shadow-sm mb-8"
        title="数据来源"
      >
        <Space size="large">
          <Statistic
            title="📝 本地面经"
            value={bySource.local ?? 0}
            suffix="道"
          />
          <Statistic
            title="🌐 牛客网"
            value={bySource.nowcoder ?? 0}
            suffix="道"
          />
        </Space>
      </Card>

      {/* ─── 知识库状态 ─────────────────────── */}
      <Card
        className="rounded-xl shadow-sm"
        title={
          <span className="flex items-center gap-2">
            <GithubOutlined /> 关联知识库
          </span>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { name: 'datawhalechina/hello-agents', status: '已关联' },
            { name: 'datawhalechina/all-in-rag', status: '已关联' },
            { name: 'datawhalechina/easy-vibe', status: '已关联' },
            { name: 'shareAI-lab/learn-claude-code', status: '已关联' },
            { name: 'xindoo/agentic-design-patterns', status: '已关联' },
          ].map((repo) => (
            <div
              key={repo.name}
              className="flex items-center justify-between p-3 bg-gray-50
                         rounded-lg"
            >
              <span className="text-sm font-mono text-gray-700">
                {repo.name}
              </span>
              <Tag color="green">{repo.status}</Tag>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
