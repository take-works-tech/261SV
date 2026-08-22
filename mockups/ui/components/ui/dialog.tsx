import * as DialogPrimitive from '@radix-ui/react-dialog'
import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Dialog({ children, open = true, onOpenChange }: { children: ReactNode; open?: boolean; onOpenChange?: (open: boolean) => void }) {
  return <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>{children}</DialogPrimitive.Root>
}

export function DialogOverlay({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <DialogPrimitive.Overlay asChild><div className={cn('fixed inset-0 z-50 bg-black/40 backdrop-blur-[1px]', className)} {...props} /></DialogPrimitive.Overlay>
}

export function DialogContent({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <DialogPrimitive.Content asChild><div className={cn('fixed left-1/2 top-1/2 z-50 grid w-full max-w-lg -translate-x-1/2 -translate-y-1/2 gap-4 rounded-lg border bg-background p-6 shadow-lg', className)} {...props}>{children}</div></DialogPrimitive.Content>
}

export function DialogFooter({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return <footer className={cn('flex flex-col-reverse gap-2 sm:flex-row sm:justify-end', className)} {...props} />
}
