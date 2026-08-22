'use client'

import * as PopoverPrimitive from '@radix-ui/react-popover'
import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Popover({ open, onOpenChange, children }: { open: boolean; onOpenChange?: (open: boolean) => void; children: ReactNode }) {
  return <PopoverPrimitive.Root open={open} onOpenChange={onOpenChange}>{children}</PopoverPrimitive.Root>
}

export function PopoverContent({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <PopoverPrimitive.Content asChild><div role="dialog" data-state="open" className={cn('z-50 rounded-md border bg-popover text-popover-foreground shadow-md outline-none', className)} {...props}>{children}</div></PopoverPrimitive.Content>
}

export function PopoverClose({ children, ...props }: HTMLAttributes<HTMLButtonElement>) {
  return <PopoverPrimitive.Close asChild><button type="button" {...props}>{children}</button></PopoverPrimitive.Close>
}
