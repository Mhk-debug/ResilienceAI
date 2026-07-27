"use client";

import React from "react";
import { Activity, LogOut, LogIn, UserPlus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { BASE_API_URL } from "@/utils/constants";

function Header() {
    const router = useRouter();
    const { user, isAuthenticated, logout } = useAuth();

    const handleLogout = async () => {
        try {
            await fetch(`${BASE_API_URL}/auth/logout`, {
                method: "POST",
                credentials: "include",
            });
        } catch {
            // Logout even if server is unreachable
        }
        logout();
        router.push("/login");
    };

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
                {isAuthenticated && user ? (
                    <>
                        <span className="hidden truncate text-xs font-medium text-primary-foreground/80 sm:block max-w-[140px]">
                            {user.email}
                        </span>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleLogout}
                            className="text-primary-foreground/70 hover:text-primary-foreground hover:bg-primary-foreground/10"
                        >
                            <LogOut className="h-4 w-4" />
                            <span className="hidden sm:inline">Logout</span>
                        </Button>
                    </>
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
