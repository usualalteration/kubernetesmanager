import * as React from "react"

import { cn } from "@/lib/utils"

interface TabsProps {
  value: string;
  onValueChange?: (value: string) => void;
  className?: string;
  children: React.ReactNode;
}

const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  ({ className, children, ...props }, ref) => (
    <div className={cn("flex flex-col", className)} {...props} ref={ref}>
      {children}
    </div>
  )
)
Tabs.displayName = "Tabs"

interface TabsListProps {
  className?: string;
  children: React.ReactNode;
}

const TabsList = React.forwardRef<HTMLDivElement, TabsListProps>(
  ({ className, children, ...props }, ref) => (
    <div
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
        className
      )}
      {...props}
      ref={ref}
    >
      {children}
    </div>
  )
)
TabsList.displayName = "TabsList"

interface TabsTriggerProps {
  value: string;
  className?: string;
  children: React.ReactNode;
  onClick?: (value: string) => void;
}

const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, children, value, ...props }, ref) => (
    <button
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm",
        className
      )}
      value={value}
      {...props}
      ref={ref}
    >
      {children}
    </button>
  )
)
TabsTrigger.displayName = "TabsTrigger"

interface TabsContentProps {
  value: string;
  className?: string;
  children: React.ReactNode;
}

const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, children, value, ...props }, ref) => (
    <div
      className={cn(
        "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      {...props}
      ref={ref}
    >
      {children}
    </div>
  )
)
TabsContent.displayName = "TabsContent"

export { Tabs, TabsList, TabsTrigger, TabsContent }