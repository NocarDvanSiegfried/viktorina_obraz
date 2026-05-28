import { expect, test } from "@playwright/test"

import { createQuizViaUi } from "../helpers/createQuiz"

const OWNER_ID = "e2e-list-actions-00000000-0000-4000-8000-000000000001"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((ownerId: string) => {
    localStorage.setItem("viktorina_owner_id", ownerId)
  }, OWNER_ID)
})

test("list card actions: open history, duplicate, archive", async ({ page }) => {
  const topic = `Stage3 Actions ${Date.now()}`
  await createQuizViaUi(page, { topic, questionCount: 3 })

  await page
    .getByRole("navigation", { name: "Разделы викторины" })
    .getByRole("link", { name: "Настройки", exact: true })
    .click()
  await page.getByLabel("Заголовок").fill(topic)
  await page.getByRole("button", { name: "Сохранить настройки" }).click()

  await page.goto("/")
  const card = page
    .locator(".quiz-card")
    .filter({ has: page.locator(".quiz-card-title", { hasText: new RegExp(`^${topic}$`) }) })
    .first()
  await expect(card).toBeVisible()

  await card.getByRole("button", { name: "Действия" }).click()
  await card.getByRole("link", { name: "История изменений" }).click()
  await expect(page).toHaveURL(/\/edit\/.*\?tab=history/)

  await page.goto("/")
  const cardAgain = page
    .locator(".quiz-card")
    .filter({ has: page.locator(".quiz-card-title", { hasText: new RegExp(`^${topic}$`) }) })
    .first()
  await cardAgain.getByRole("button", { name: "Действия" }).click()
  await cardAgain.getByRole("button", { name: "Дублировать" }).click()
  await expect(
    page.locator(".quiz-card").filter({ hasText: `${topic} (копия)` })
  ).toHaveCount(1)

  page.once("dialog", (dialog) => dialog.accept())
  await cardAgain.getByRole("button", { name: "Действия" }).click()
  await cardAgain.getByRole("button", { name: "Архивировать" }).click()
  await expect(
    page
      .locator(".quiz-card-title")
      .filter({ hasText: new RegExp(`^${topic}$`) })
  ).toHaveCount(0)
})
