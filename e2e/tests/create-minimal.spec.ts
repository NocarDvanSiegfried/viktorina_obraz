import { expect, test } from "@playwright/test"

import {
  createQuizViaUi,
  fillMinimalCreateForm,
  generateQuizWithAi,
} from "../helpers/createQuiz"

const OWNER_ID = "e2e-create-minimal-00000000-0000-4000-8000-000000000001"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((ownerId: string) => {
    localStorage.setItem("viktorina_owner_id", ownerId)
  }, OWNER_ID)
})

test("create: AI button visible on single screen", async ({ page }) => {
  await page.goto("/create")
  await expect(
    page.getByRole("heading", { name: "Новая викторина" })
  ).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Сгенерировать с ИИ" })
  ).toBeVisible()
  await expect(page.getByRole("button", { name: "Далее" })).toHaveCount(0)
})

test("create: generates and opens preview tab", async ({ page }) => {
  await createQuizViaUi(page, {
    topic: "Клетка minimal",
    questionCount: 3,
  })
  await expect(page).toHaveURL(/tab=preview/)
  await expect(page.getByRole("heading", { name: "Быстрый просмотр" })).toBeVisible()
  await expect(page.locator(".question-preview-list")).toBeVisible()
})

test("create: type preset single only", async ({ page }) => {
  await page.goto("/create")
  await fillMinimalCreateForm(page, { topic: "Типы", questionCount: 3 })
  await generateQuizWithAi(page)
  await expect(page.locator(".question-preview-item").first()).toBeVisible()
})
