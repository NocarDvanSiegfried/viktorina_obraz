/**
 * UI-10: accessibility landmarks, mobile layout, debug panel hidden by default.
 */

import { expect, test } from "@playwright/test"

const OWNER_ID = "e2e-ui10-owner-00000000-0000-4000-8000-000000000001"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((ownerId: string) => {
    localStorage.setItem("viktorina_owner_id", ownerId)
  }, OWNER_ID)
})

test("a11y: skip link and main landmark on home", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByRole("link", { name: "Перейти к содержимому" })).toBeAttached()
  await expect(page.locator("#main-content")).toBeVisible()
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()
})

test("a11y: debug panel collapsed on list page", async ({ page }) => {
  await page.goto("/")
  const debugPanel = page.locator("details.debug-panel")
  if ((await debugPanel.count()) > 0) {
    await expect(debugPanel.first()).not.toHaveAttribute("open", "")
  }
})

test("mobile: list page without horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 })
  await page.goto("/")
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()

  const hasHorizontalOverflow = await page.evaluate(() => {
    const root = document.documentElement
    return root.scrollWidth > root.clientWidth + 1
  })
  expect(hasHorizontalOverflow).toBe(false)
})

test("mobile: create minimal form visible", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto("/create")
  await expect(
    page.getByRole("heading", { name: "Новая викторина" })
  ).toBeVisible()
  await expect(page.getByPlaceholder("Вставьте текст урока...")).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Сгенерировать с ИИ" })
  ).toBeVisible()
})
