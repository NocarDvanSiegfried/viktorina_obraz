import type { ReactNode } from "react"
import { Link } from "react-router-dom"

type PageHeaderProps = {
  title: string
  subtitle?: string
  backTo?: string
  backLabel?: string
  actions?: ReactNode
}

export function PageHeader({
  title,
  subtitle,
  backTo,
  backLabel = "← Назад",
  actions,
}: PageHeaderProps) {
  return (
    <header className="page-header">
      {backTo && (
        <p className="page-header-back">
          <Link to={backTo}>{backLabel}</Link>
        </p>
      )}
      <div className="page-header-row">
        <div className="page-header-titles">
          <h1>{title}</h1>
          {subtitle && <p className="subtitle page-header-subtitle">{subtitle}</p>}
        </div>
        {actions && <div className="page-header-actions">{actions}</div>}
      </div>
    </header>
  )
}
