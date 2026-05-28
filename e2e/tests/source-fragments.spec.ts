/**
 * Day 21: API returns fragment catalog with preview (no browser UI — avoids port conflicts).
 */

import { expect, test } from "@playwright/test"

const OWNER_ID = "e2e-source-fragments-owner"
const SOURCE_TEXT =
  "Клетка — основная структурная единица. Мембрана отделяет цитоплазму от среды."

test("API: GET /quiz/{id} includes fragments with preview", async ({ request }) => {
  const formBody = new URLSearchParams()
  formBody.set("owner_id", OWNER_ID)
  formBody.set("subject", "Biology")
  formBody.set("grade", "8")
  formBody.set("topic", "Cell")
  formBody.set("question_count", "1")
  formBody.set("difficulty", "easy")
  formBody.append("question_types", "single_choice")
  formBody.set("source_text", SOURCE_TEXT)

  const apiBase = process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8001"

  const generated = await request.post(`${apiBase}/quiz/generate-from-materials`, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    data: formBody.toString(),
    timeout: 120_000,
  })
  expect(generated.ok()).toBeTruthy()
  const quizId = ((await generated.json()) as { quiz_id: string }).quiz_id

  const detail = await request.get(`${apiBase}/quiz/${quizId}`, {
    params: { owner_id: OWNER_ID },
  })
  expect(detail.ok()).toBeTruthy()

  const body = (await detail.json()) as {
    fragments?: { id: string; preview: string; source_type: string }[]
  }
  expect(body.fragments?.length).toBeGreaterThan(0)

  const manual = body.fragments?.find((item) => item.id === "manual_1")
  expect(manual?.preview).toContain("Клетка")
  expect(manual?.source_type).toBe("manual_text")
})
