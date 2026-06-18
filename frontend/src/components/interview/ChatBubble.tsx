// ============================================================
// ChatBubble — 单条消息气泡（支持 Markdown + 代码高亮 + 流式光标）
// ============================================================

import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { ChatMessage } from '../../types'

interface Props {
  message: ChatMessage
  streaming?: boolean
}

export default function ChatBubble({ message, streaming }: Props) {
  const isInterviewer = message.role === 'interviewer'
  const isCandidate = message.role === 'candidate'

  return (
    <div
      className={`flex ${isCandidate ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-5 py-3 ${
          isInterviewer
            ? 'bg-gray-100 text-gray-900 rounded-tl-sm'
            : 'bg-blue-500 text-white rounded-tr-sm'
        }`}
      >
        {/* 角色标签 */}
        <div
          className={`text-xs mb-1 font-medium ${
            isInterviewer ? 'text-blue-500' : 'text-blue-100'
          }`}
        >
          {isInterviewer ? '🤖 AI 面试官' : '👤 你'}
        </div>

        {/* 消息内容 */}
        <div className={`prose max-w-none text-sm leading-relaxed ${
          isCandidate ? 'prose-invert [&_code]:text-white [&_code]:bg-white/20' : ''
        }`}>
          <ReactMarkdown
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '')
                const codeStr = String(children).replace(/\n$/, '')
                if (!match) {
                  return (
                    <code
                      className={`${className || ''} px-1 py-0.5 rounded text-xs ${
                        isCandidate
                          ? 'bg-white/20 text-white'
                          : 'bg-gray-200 text-gray-800'
                      }`}
                      {...props}
                    >
                      {children}
                    </code>
                  )
                }
                return (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={match[1]}
                    PreTag="pre"
                    customStyle={{
                      borderRadius: 8,
                      fontSize: 13,
                      padding: '12px 16px',
                      marginTop: 8,
                      marginBottom: 8,
                    }}
                  >
                    {codeStr}
                  </SyntaxHighlighter>
                )
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* 流式光标 */}
        {streaming && (
          <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-0.5 align-text-bottom" />
        )}

        {/* 时间戳 */}
        <div
          className={`text-xs mt-2 ${
            isInterviewer ? 'text-gray-400' : 'text-blue-200'
          }`}
        >
          {new Date(message.timestamp).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  )
}
