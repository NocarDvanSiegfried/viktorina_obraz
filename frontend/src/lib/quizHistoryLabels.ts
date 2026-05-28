/** Human-readable labels for quiz version history (UX-6). */

const VERSION_EVENT_LABELS: Record<string, string> = {
  "Создание викторины": "Создано из материала",
  "Изменение настроек": "Изменение настроек",
  "Добавление вопроса": "Изменение вопросов",
  "Изменение вопроса": "Изменение вопросов",
  "Удаление вопроса": "Изменение вопросов",
  "Изменение порядка вопросов": "Изменение вопросов",
  "Пересоздание вопроса (ИИ)": "Пересоздание вопроса (ИИ)",
}

export function formatVersionEventLabel(label: string | null | undefined): string {
  const raw = (label ?? "").trim()
  if (!raw) return "Изменение викторины"
  return VERSION_EVENT_LABELS[raw] ?? raw
}
