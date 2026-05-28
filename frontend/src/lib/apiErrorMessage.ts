/** Human-readable API/network errors for teachers (UI-9). */

const GIGACHAT_PATTERNS = [
  "gigachat",
  "не удалось сгенерировать викторину",
  "не удалось пересоздать вопрос",
  "502",
  "bad gateway",
]

const NETWORK_PATTERNS = [
  "failed to fetch",
  "networkerror",
  "network error",
  "load failed",
]

export function mapErrorMessage(
  error: unknown,
  fallback = "Что-то пошло не так. Попробуйте ещё раз."
): string {
  const raw =
    error instanceof Error
      ? error.message
      : typeof error === "string"
        ? error
        : ""

  const trimmed = raw.trim()
  if (!trimmed) return fallback

  const lower = trimmed.toLowerCase()

  if (GIGACHAT_PATTERNS.some((pattern) => lower.includes(pattern))) {
    return (
      "Сервис ИИ временно недоступен. Подождите минуту и попробуйте снова. " +
      "Если ошибка повторяется — упростите материал или используйте текст вместо файла."
    )
  }

  if (lower.includes("429") || lower.includes("слишком много")) {
    return "Слишком много запросов. Подождите минуту и повторите действие."
  }

  if (NETWORK_PATTERNS.some((pattern) => lower.includes(pattern))) {
    return "Нет связи с сервером. Проверьте интернет и обновите страницу."
  }

  if (lower.includes("403") || lower.includes("доступ запрещён")) {
    return "Нет доступа к этой викторине. Откройте её из своего списка."
  }

  if (lower.includes("404") || lower.includes("не найден")) {
    return "Викторина не найдена. Проверьте ссылку или создайте новую."
  }

  if (trimmed.includes("Traceback") || trimmed.includes("Exception:")) {
    return fallback
  }

  return trimmed
}
