import type { ButtonHTMLAttributes, ReactNode } from "react"
import { Link, type LinkProps } from "react-router-dom"

type ButtonVariant = "primary" | "secondary" | "ghost"

type ButtonBaseProps = {
  variant?: ButtonVariant
  children: ReactNode
  className?: string
}

type ButtonAsButton = ButtonBaseProps &
  ButtonHTMLAttributes<HTMLButtonElement> & {
    as?: "button"
    to?: never
  }

type ButtonAsLink = ButtonBaseProps &
  Omit<LinkProps, "className" | "children"> & {
    as: "link"
    to: string
  }

export type ButtonProps = ButtonAsButton | ButtonAsLink

function buttonClassName(variant: ButtonVariant, extra?: string): string {
  return ["btn", `btn-${variant}`, extra].filter(Boolean).join(" ")
}

export function Button(props: ButtonProps) {
  const { variant = "primary", children, className } = props
  const classes = buttonClassName(variant, className)

  if (props.as === "link") {
    const { as: _as, variant: _v, to, ...linkProps } = props
    return (
      <Link to={to} className={classes} {...linkProps}>
        {children}
      </Link>
    )
  }

  const { as: _as, variant: _v, to: _to, ...buttonProps } = props
  return (
    <button type="button" className={classes} {...buttonProps}>
      {children}
    </button>
  )
}
