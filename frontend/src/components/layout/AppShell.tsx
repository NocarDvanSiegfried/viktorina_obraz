import { NavLink, Outlet, useLocation } from "react-router-dom"

import { SkipLink } from "@/components/layout/SkipLink"

function navClassName({ isActive }: { isActive: boolean }): string {
  return isActive ? "app-nav-link app-nav-link-active" : "app-nav-link"
}

export function AppShell() {
  const { pathname } = useLocation()
  const isStudentRoute = pathname.startsWith("/student/")

  return (
    <div className="app-shell">
      <SkipLink />
      <header className="app-header">
        <div className="app-header-inner">
          {isStudentRoute ? (
            <span className="app-brand">Викторина</span>
          ) : (
            <NavLink to="/" className="app-brand">
              Викторина
            </NavLink>
          )}
          {!isStudentRoute && (
            <nav className="app-nav" aria-label="Основная навигация">
              <NavLink to="/" end className={navClassName}>
                Мои викторины
              </NavLink>
              <NavLink to="/create" className={navClassName}>
                Создать викторину
              </NavLink>
              <NavLink to="/history" className={navClassName}>
                История
              </NavLink>
            </nav>
          )}
        </div>
      </header>

      <main id="main-content" className="app-main" tabIndex={-1}>
        <Outlet />
      </main>

      <footer className="app-footer">
        <p>Школьные викторины из учебных материалов</p>
      </footer>
    </div>
  )
}
