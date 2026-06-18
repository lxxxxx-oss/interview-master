// ============================================================
// App — React Router 路由配置
// ============================================================

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import AppLayout from './components/AppLayout'
import HomePage from './pages/HomePage'
import QuestionDetailPage from './components/QuestionDetail'
// import AdminPage from './pages/AdminPage'       // TODO: 上线时取消注释
// import InterviewPage from './pages/InterviewPage' // TODO: 上线时取消注释

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
            {/* TODO: 上线时取消注释
            <Route path="/interview" element={<InterviewPage />} />
            <Route path="/admin" element={<AdminPage />} />
            */}
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
