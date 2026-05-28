import type { ReactNode } from "react"

type BadgeVariant = "neutral" | "difficulty" | "status"

type BadgeProps = {
  children: ReactNode
  variant?: BadgeVariant
  className?: string
}

export function Badge({ children, variant = "neutral", className }: BadgeProps) {
  return (
    <span className={["badge", `badge-${variant}`, className].filter(Boolean).join(" ")}>
      {children}
    </span>
  )
}
