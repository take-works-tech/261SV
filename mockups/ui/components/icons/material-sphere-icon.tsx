import { forwardRef } from 'react'
import type { LucideProps } from 'lucide-react'

export const MaterialSphereIcon = forwardRef<SVGSVGElement, LucideProps>(function MaterialSphereIcon(
  { color = 'currentColor', size = 24, strokeWidth = 2, absoluteStrokeWidth = false, children, ...props },
  ref,
) {
  const resolvedStrokeWidth = absoluteStrokeWidth && typeof size === 'number'
    ? (Number(strokeWidth) * 24) / size
    : strokeWidth

  return (
    <svg
      ref={ref}
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={resolvedStrokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      <circle cx="12" cy="12" r="9" />
      <path d="M12.3 3.1c1.9 2 2.7 4.8 2.1 7.6-.9 4.4-4.5 7.8-8.9 8.6" />
      <path d="M7.4 7.7c.8-.9 1.8-1.5 3-1.8" />
      {children}
    </svg>
  )
})
