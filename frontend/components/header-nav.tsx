"use client";

import React from "react";
import { Activity, LogIn, UserPlus } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import ProfileButton from "./profile-button";

const NAV_LINKS = [
    { href: "/form", label: "New Assessment" },
    { href: "/assessments", label: "Assessments" },
];

function HeaderNav() {
    const { isAuthenticated, isLoading } = useAuth();
    const pathname = usePathname();

    const isActive = (href: string) =>
        href === "/" ? pathname === href : pathname.startsWith(href);

    return (
        <header className="relative border-b border-primary-foreground/10 bg-[hsl(224_58%_18%)] px-6 py-4 md:px-10 md:py-5 shadow-lg">
            {/* Absolutely-centered nav — its center is the header's center,
                independent of how wide the brand / auth sides are. */}
            <nav
                aria-label="Main navigation"
                className="absolute left-1/2 top-1/2 hidden -translate-x-1/2 -translate-y-1/2 items-center md:flex"
            >
                <ul className="flex items-center gap-1">
                    {NAV_LINKS.map(({ href, label }) => {
                        const active = isActive(href);
                        return (
                            <li key={href} className="relative">
                                <Link
                                    href={href}
                                    aria-current={active ? "page" : undefined}
                                    className={`relative rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                                        active
                                            ? "text-primary-foreground"
                                            : "text-primary-foreground/70 hover:bg-primary-foreground/10 hover:text-primary-foreground"
                                    }`}
                                >
                                    {label}
                                </Link>
                                {/* Static accent underline on the active link */}
                                {active && (
                                    <span
                                        aria-hidden
                                        className="pointer-events-none absolute inset-x-3 -bottom-1.5 h-0.5 rounded-full bg-sky-400"
                                    />
                                )}
                            </li>
                        );
                    })}
                </ul>
            </nav>

            <div className="flex items-center justify-between gap-4">
                {/* Left: brand */}
                <Link href="/" className="flex flex-col gap-0.5 min-w-0">
                    <div className="flex items-center gap-2.5">
                        <Activity className="h-5 w-5 text-primary-foreground opacity-80 shrink-0" />
                        <h1 className="text-lg font-bold tracking-tight text-primary-foreground md:text-xl truncate">
                            Earthquake Risk Assessment AI
                        </h1>
                    </div>
                    <p className="text-xs font-medium tracking-widest text-primary-foreground/50 pl-7 uppercase">
                        codeTrio &nbsp;·&nbsp; STIMU
                    </p>
                </Link>

                {/* Right: auth actions */}
                <div className="flex items-center gap-3">
                    {isLoading ? (
                        // Skeleton while auth check is running — no flicker
                        <div className="flex items-center gap-2">
                            <div className="h-8 w-20 animate-pulse rounded-md bg-primary-foreground/10" />
                        </div>
                    ) : isAuthenticated ? (
                        <ProfileButton />
                    ) : (
                        <>
                            <Link href="/login">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="text-primary-foreground/70 hover:text-primary-foreground hover:bg-primary-foreground/10"
                                >
                                    <LogIn className="h-4 w-4" />
                                    <span className="hidden sm:inline">Login</span>
                                </Button>
                            </Link>
                            <Link href="/register">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="text-primary-foreground/70 hover:text-primary-foreground hover:bg-primary-foreground/10"
                                >
                                    <UserPlus className="h-4 w-4" />
                                    <span className="hidden sm:inline">Register</span>
                                </Button>
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}

export default HeaderNav;