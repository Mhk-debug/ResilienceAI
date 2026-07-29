"use client";

import { Menu } from "@base-ui/react/menu";
import { cn } from "@/lib/utils";

function DropdownMenu({ children, ...props }: Menu.Root.Props) {
  return <Menu.Root {...props}>{children}</Menu.Root>;
}

function DropdownMenuTrigger({ children, className, ...props }: Menu.Trigger.Props) {
  return (
    <Menu.Trigger className={cn("outline-none", className)} {...props}>
      {children}
    </Menu.Trigger>
  );
}

interface DropdownMenuContentProps extends Menu.Popup.Props {
  align?: "start" | "center" | "end";
  sideOffset?: number;
}

function DropdownMenuContent({
  children,
  className,
  align = "end",
  sideOffset = 4,
  ...props
}: DropdownMenuContentProps) {
  return (
    <Menu.Portal>
      <Menu.Positioner align={align} sideOffset={sideOffset}>
        <Menu.Popup
          className={cn(
            "z-50 min-w-[200px] overflow-hidden rounded-xl border border-border bg-popover p-1 shadow-lg",
            "origin-[var(--transform-origin)] transition-[transform,opacity]",
            "data-[ending-style]:scale-90 data-[ending-style]:opacity-0 data-[starting-style]:scale-90 data-[starting-style]:opacity-0",
            "data-[side=none]:opacity-100",
            className,
          )}
          {...props}
        >
          {children}
        </Menu.Popup>
      </Menu.Positioner>
    </Menu.Portal>
  );
}

function DropdownMenuItem({
  children,
  className,
  ...props
}: Menu.Item.Props) {
  return (
    <Menu.Item
      className={cn(
        "relative flex cursor-default select-none items-center gap-2 rounded-lg px-3 py-2 text-sm outline-none transition-colors",
        "data-[highlighted]:bg-muted data-[highlighted]:text-foreground",
        "data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className,
      )}
      {...props}
    >
      {children}
    </Menu.Item>
  );
}

function DropdownMenuSeparator({ className }: { className?: string }) {
  return (
    <Menu.Separator
      className={cn("-mx-1 my-1 h-px bg-border", className)}
    />
  );
}

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
};
