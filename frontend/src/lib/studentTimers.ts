/** Client countdown helpers (day 12). */

export function remainingSeconds(
  limitSeconds: number | null | undefined,
  startedAtIso: string | null | undefined,
  nowMs: number
): number | null {
  if (limitSeconds == null || limitSeconds <= 0 || !startedAtIso) {
    return null
  }
  const started = Date.parse(startedAtIso)
  if (Number.isNaN(started)) {
    return null
  }
  const elapsed = Math.floor((nowMs - started) / 1000)
  return Math.max(0, limitSeconds - elapsed)
}

export function formatCountdown(seconds: number | null): string {
  if (seconds === null) {
    return "не задан"
  }
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toString().padStart(2, "0")}`
}

export function isTimeExpired(remaining: number | null): boolean {
  return remaining !== null && remaining <= 0
}
