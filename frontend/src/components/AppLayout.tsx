// ============================================================
// Layout — Header + Content wrapper
// ============================================================

import { Layout, Menu } from 'antd'
import { HomeOutlined, SettingOutlined, RobotOutlined } from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Header, Content } = Layout

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { key: '/', icon: <HomeOutlined />, label: '面经题库' },
    { key: '/interview', icon: <RobotOutlined />, label: '模拟面试' },
    { key: '/admin', icon: <SettingOutlined />, label: '管理' },
  ]

  const selectedKey =
    location.pathname === '/admin' ? '/admin'
    : location.pathname.startsWith('/interview') ? '/interview'
    : '/'

  return (
    <Layout className="min-h-screen">
      {/* ─── 顶部导航 ───────────────────────── */}
      <Header
        style={{
          background: '#fff',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          padding: '0 24px',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        {/* Logo */}
        <div
          className="flex items-center gap-2 cursor-pointer mr-8"
          onClick={() => navigate('/')}
        >
          <RobotOutlined
            style={{ fontSize: 24, color: '#1677ff' }}
          />
          <span className="text-lg font-bold text-gray-900">
            Agent 面试通
          </span>
        </div>

        {/* 导航 */}
        <Menu
          mode="horizontal"
          selectedKeys={[selectedKey]}
          items={navItems}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, border: 'none' }}
        />
      </Header>

      {/* ─── 内容区 ──────────────────────────── */}
      <Content className="p-6 max-w-[1400px] mx-auto w-full">
        <Outlet />
      </Content>
    </Layout>
  )
}
