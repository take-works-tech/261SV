'use client'

import * as TabsPrimitive from '@radix-ui/react-tabs'
import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Tabs({ value, defaultValue, onValueChange, children, className, ...props }: Omit<HTMLAttributes<HTMLDivElement>, 'dir'> & { value?: string; defaultValue?: string; onValueChange?: (value: string) => void }) {
  return <TabsPrimitive.Root value={value} defaultValue={defaultValue} onValueChange={onValueChange} className={className} {...props}>{children}</TabsPrimitive.Root>
}

export function TabsList({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <TabsPrimitive.List className={cn('inline-flex items-center rounded-md bg-muted p-1 text-muted-foreground', className)} {...props} />
}

export function TabsTrigger({ value, children, className, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { value: string; children: ReactNode }) {
  return <TabsPrimitive.Trigger value={value} className={cn('inline-flex items-center justify-center rounded px-3 py-1.5 type-body font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring', className)} {...props}>{children}</TabsPrimitive.Trigger>
}

export function TabsContent({ value, className, children, ...props }: HTMLAttributes<HTMLDivElement> & { value: string }) {
  return <TabsPrimitive.Content value={value} className={className} {...props}>{children}</TabsPrimitive.Content>
}
