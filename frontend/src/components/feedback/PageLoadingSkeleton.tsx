import { Skeleton } from "@/components/feedback/Skeleton"

type PageLoadingSkeletonProps = {
  variant?: "list" | "detail" | "results"
}

export function PageLoadingSkeleton({ variant = "detail" }: PageLoadingSkeletonProps) {
  if (variant === "list") {
    return (
      <div className="page-loading-skeleton" aria-busy="true" aria-label="Загрузка">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="skeleton-card">
            <Skeleton height="1.25rem" width="55%" />
            <Skeleton height="0.875rem" width="35%" />
            <Skeleton height="0.875rem" width="70%" />
          </div>
        ))}
      </div>
    )
  }

  if (variant === "results") {
    return (
      <div className="page-loading-skeleton" aria-busy="true" aria-label="Загрузка">
        <div className="skeleton-toolbar">
          <Skeleton height="2.5rem" width="10rem" />
          <Skeleton height="2.5rem" width="14rem" />
        </div>
        <div className="skeleton-kpi-row">
          <Skeleton height="5rem" />
          <Skeleton height="5rem" />
          <Skeleton height="5rem" />
        </div>
        <Skeleton height="6rem" />
        <Skeleton height="8rem" />
      </div>
    )
  }

  return (
    <div className="page-loading-skeleton" aria-busy="true" aria-label="Загрузка">
      <Skeleton height="1.75rem" width="60%" />
      <Skeleton height="1rem" width="80%" />
      <Skeleton height="12rem" />
      <Skeleton height="8rem" />
    </div>
  )
}
