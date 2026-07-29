"use client";

import React from "react";
import { Activity, LogIn, UserPlus } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import ProfileButton from "./profile-button";

function Header() {
    const { isAuthenticated, isLoading } = useAuth();

    return (
        <header className="bg-[hsl(224_58%_18%)] px-6 py-4 md:px-10 md:py-5 flex items-center justify-between shadow-lg">
            <div className="flex flex-col gap-0.5">
                <div className="flex items-center gap-2.5">
                    <Activity className="h-5 w-5 text-primary-foreground opacity-80" />
                    <h1 className="text-lg font-bold tracking-tight text-primary-foreground md:text-xl">
                        Earthquake Risk Assessment AI
                    </h1>
                </div>
                <p className="text-xs font-medium tracking-widest text-primary-foreground/50 pl-7 uppercase">
                    codeTrio &nbsp;·&nbsp; STIMU
                </p>
            </div>

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
        </header>
    );
}

export default Header;
