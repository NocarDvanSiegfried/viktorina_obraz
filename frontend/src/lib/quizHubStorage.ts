const SETTINGS_SAVED_KEY = "quiz_settings_saved"
const SHARE_COPIED_KEY = "quiz_share_copied"

function readMap(key: string): Record<string, boolean> {
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Record<string, boolean>
    return typeof parsed === "object" && parsed != null ? parsed : {}
  } catch {
    return {}
  }
}

function writeMap(key: string, map: Record<string, boolean>): void {
  sessionStorage.setItem(key, JSON.stringify(map))
}

export function markSettingsSaved(quizId: string): void {
  const map = readMap(SETTINGS_SAVED_KEY)
  map[quizId] = true
  writeMap(SETTINGS_SAVED_KEY, map)
}

export function isSettingsSaved(quizId: string): boolean {
  return Boolean(readMap(SETTINGS_SAVED_KEY)[quizId])
}

export function markShareCopied(quizId: string): void {
  const map = readMap(SHARE_COPIED_KEY)
  map[quizId] = true
  writeMap(SHARE_COPIED_KEY, map)
}

export function isShareCopied(quizId: string): boolean {
  return Boolean(readMap(SHARE_COPIED_KEY)[quizId])
}
