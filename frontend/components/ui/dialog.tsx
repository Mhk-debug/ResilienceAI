"use client";

import { Dialog as DialogPrimitive } from "@base-ui/react/dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

function Dialog({ children, ...props }: DialogPrimitive.Root.Props) {
  return <DialogPrimitive.Root {...props}>{children}</DialogPrimitive.Root>;
}

function DialogTrigger({ children, className, ...props }: DialogPrimitive.Trigger.Props) {
  return (
    <DialogPrimitive.Trigger className={cn("outline-none", className)} {...props}>
      {children}
    </DialogPrimitive.Trigger>
  );
}

function DialogContent({
  children,
  className,
  title,
  ...props
}: DialogPrimitive.Popup.Props & { title?: string }) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Backdrop className="fixed inset-0 z-50 bg-black/40 data-[ending-style]:opacity-0 data-[starting-style]:opacity-0 transition-opacity" />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <DialogPrimitive.Popup
          className={cn(
            "relative w-full max-w-md rounded-2xl border bg-card p-6 shadow-xl",
            "data-[ending-style]:scale-90 data-[ending-style]:opacity-0 data-[starting-style]:scale-90 data-[starting-style]:opacity-0",
            "transition-[transform,opacity] duration-150",
            className,
          )}
          {...props}
        >
          {title && (
            <DialogPrimitive.Title className="mb-1 text-lg font-semibold text-foreground">
              {title}
            </DialogPrimitive.Title>
          )}
          <DialogPrimitive.Close className="absolute right-4 top-4 text-muted-foreground hover:text-foreground transition-colors">
            <X className="h-4 w-4" />
          </DialogPrimitive.Close>
          {children}
        </DialogPrimitive.Popup>
      </div>
    </DialogPrimitive.Portal>
  );
}

function DialogDescription({ children, className, ...props }: DialogPrimitive.Description.Props) {
  return (
    <DialogPrimitive.Description
      className={cn("mb-4 text-sm text-muted-foreground", className)}
      {...props}
    >
      {children}
    </DialogPrimitive.Description>
  );
}

function DialogClose({
  children,
  className,
  ...props
}: DialogPrimitive.Close.Props) {
  return (
    <DialogPrimitive.Close className={cn("outline-none", className)} {...props}>
      {children}
    </DialogPrimitive.Close>
  );
}

export { Dialog, DialogTrigger, DialogContent, DialogDescription, DialogClose };
