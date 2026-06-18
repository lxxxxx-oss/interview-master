// ============================================================
// InterviewPage — 模拟面试页面容器
// ============================================================

import { useInterviewStore } from '../store/interviewStore'
import InterviewSetup from '../components/interview/InterviewSetup'
import InterviewChat from '../components/interview/InterviewChat'

export default function InterviewPage() {
  const { session, startInterview } = useInterviewStore()

  if (!session) {
    return <InterviewSetup onStart={startInterview} />
  }

  return <InterviewChat />
}
