// ============================================================
// App — React Router 路由配置
// ============================================================

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import AppLayout from './components/AppLayout'
import HomePage from './pages/HomePage'
import QuestionDetailPage from './components/QuestionDetail'
import InterviewPage from './pages/InterviewPage'
// import AdminPage from './pages/AdminPage'

// 环境变量开关 — 生产环境通过 .env.production 控制功能可见性
const ENABLE_INTERVIEW = import.meta.env.VITE_ENABLE_INTERVIEW !== 'false'
// const ENABLE_ADMIN = import.meta.env.VITE_ENABLE_ADMIN === 'true'

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 8,
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/question/:id" element={<QuestionDetailPage />} />
            {ENABLE_INTERVIEW && (
              <Route path="/interview" element={<InterviewPage />} />
            )}
            {/* {ENABLE_ADMIN && (
              <Route path="/admin" element={<AdminPage />} />
            )} */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
