import * as React from "react"
import { Toaster as SonnerToaster, toast } from "sonner"
import { cva } from "class-variance-authority"

import { cn } from "@/lib/utils"

const toastVariants = cva(
  "group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all",
  {
    variants: {
      variant: {
        default: "border bg-background text-foreground",
        destructive:
          "destructive group border-destructive bg-destructive text-destructive-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Toaster({ ...props }) {
  return (
    <SonnerToaster
      className="toaster group"
      toastOptions={{
        classNames: {
          toast: cn(toastVariants({ variant: "default" })),
          description: "group-[.toast]:text-muted-foreground",
          actionButton:
            "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton:
            "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground",
          error: cn(toastVariants({ variant: "destructive" })),
        },
      }}
      {...props}
    />
  )
}

export { Toaster, toast as useToast }
