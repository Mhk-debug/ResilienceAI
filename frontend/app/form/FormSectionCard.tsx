import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type FormSectionCardProps = {
    title: string;
    desc: string;
    Icon: LucideIcon;
    children: ReactNode;
    className?: string;
};

function FormSectionCard({
    title,
    desc,
    Icon,
    children,
    className
}: FormSectionCardProps) {
    return (
        <div className="rounded-xl bg-card border border-border shadow-card overflow-hidden">
            <div className="flex items-center gap-3 px-5 py-4 border-b border-border bg-muted/30">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="h-4 w-4 text-primary" />
                </span>
                <div>
                    <p className="text-sm font-semibold text-foreground">
                        {title}
                    </p>
                    <p className="text-xs text-muted-foreground">{desc}</p>
                </div>
            </div>
            <div className={className || "px-5 py-5 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4"}>
                {children}
            </div>
        </div>
    );
}

export default FormSectionCard;
