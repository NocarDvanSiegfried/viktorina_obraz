import { expect, test } from "@playwright/test"

import { createQuizViaUi } from "../helpers/createQuiz"

const OWNER_ID = "e2e-history-delete-00000000-0000-4000-8000-000000000001"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((ownerId: string) => {
    localStorage.setItem("viktorina_owner_id", ownerId)
  }, OWNER_ID)
})

test("history screen is separate and opens quiz history tab", async ({ page }) => {
  await createQuizViaUi(page, { topic: "История отдельно", questionCount: 3 })

  await page.goto("/history")
  await expect(page.getByRole("heading", { name: "История викторин" })).toBeVisible()
  await expect(page.getByRole("link", { name: "Открыть историю изменений" }).first()).toBeVisible()

  await page.getByRole("link", { name: "Открыть историю изменений" }).first().click()
  await expect(page).toHaveURL(/\/edit\/.*\?tab=history/)
  await expect(page.getByRole("heading", { name: "История изменений" })).toBeVisible()
})

test("quiz soft-delete from settings hides quiz", async ({ page }) => {
  await createQuizViaUi(page, { topic: "Удаляемая викторина", questionCount: 3 })

  const editUrl = page.url()
  const quizId = editUrl.match(/\/edit\/([^/?#]+)/)?.[1]
  expect(quizId).toBeTruthy()

  await page
    .getByRole("navigation", { name: "Разделы викторины" })
    .getByRole("link", { name: "Настройки", exact: true })
    .click()

  page.once("dialog", (dialog) => dialog.accept())
  await page.getByRole("button", { name: "Удалить викторину" }).click()
  await expect(page).toHaveURL("/")
  await expect(page.getByRole("heading", { name: "Ваши викторины" })).toBeVisible()

  await page.goto(`/edit/${quizId}`)
  await expect(page.getByText("Викторина не найдена")).toBeVisible()
})
