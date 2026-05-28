type SkeletonProps = {
  className?: string
  width?: string
  height?: string
}

export function Skeleton({ className = "", width, height }: SkeletonProps) {
  const style = {
    width,
    height,
  }

  return (
    <div
      className={`skeleton ${className}`.trim()}
      style={style}
      aria-hidden="true"
    />
  )
}
