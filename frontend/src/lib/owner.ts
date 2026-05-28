const OWNER_STORAGE_KEY = "viktorina_owner_id"

export function getOrCreateOwnerId(): string {
  const existing = localStorage.getItem(OWNER_STORAGE_KEY)
  if (existing) {
    return existing
  }

  const created = crypto.randomUUID()
  localStorage.setItem(OWNER_STORAGE_KEY, created)
  return created
}

export function getOwnerId(): string | null {
  return localStorage.getItem(OWNER_STORAGE_KEY)
}
