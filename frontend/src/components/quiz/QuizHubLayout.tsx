import type { ReactNode } from "react"
import { Link, useSearchParams } from "react-router-dom"

export const QUIZ_HUB_MAIN_TABS = [
  { id: "preview", label: "Быстрый просмотр" },
  { id: "questions", label: "Вопросы" },
  { id: "settings", label: "Настройки" },
  { id: "results", label: "Результаты" },
] as const

export const QUIZ_HUB_MORE_TABS = [
  { id: "sources", label: "Источники" },
  { id: "history", label: "История" },
] as const

export const QUIZ_HUB_TABS = [...QUIZ_HUB_MAIN_TABS, ...QUIZ_HUB_MORE_TABS] as const

export type QuizHubTabId = (typeof QUIZ_HUB_TABS)[number]["id"]

export function getActiveHubTab(searchParams: URLSearchParams): QuizHubTabId {
  const value = searchParams.get("tab")
  if (QUIZ_HUB_TABS.some((tab) => tab.id === value)) {
    return value as QuizHubTabId
  }
  return "preview"
}

type QuizHubLayoutProps = {
  quizId: string
  children: ReactNode
}

export function QuizHubLayout({ quizId, children }: QuizHubLayoutProps) {
  const [searchParams] = useSearchParams()
  const activeTab = getActiveHubTab(searchParams)

  return (
    <div className="quiz-hub">
      <nav className="quiz-hub-tabs" aria-label="Разделы викторины">
        {QUIZ_HUB_MAIN_TABS.map((tab) => (
          <Link
            key={tab.id}
            to={`/edit/${quizId}?tab=${tab.id}`}
            className={
              activeTab === tab.id ? "quiz-hub-tab quiz-hub-tab-active" : "quiz-hub-tab"
            }
            aria-current={activeTab === tab.id ? "page" : undefined}
          >
            {tab.label}
          </Link>
        ))}
      </nav>
      <nav className="quiz-hub-tabs quiz-hub-tabs-more" aria-label="Дополнительно">
        {QUIZ_HUB_MORE_TABS.map((tab) => (
          <Link
            key={tab.id}
            to={`/edit/${quizId}?tab=${tab.id}`}
            className={
              activeTab === tab.id
                ? "quiz-hub-tab quiz-hub-tab-active quiz-hub-tab-more"
                : "quiz-hub-tab quiz-hub-tab-more"
            }
            aria-current={activeTab === tab.id ? "page" : undefined}
          >
            {tab.label}
          </Link>
        ))}
      </nav>
      <div className="quiz-hub-panel">{children}</div>
    </div>
  )
}
