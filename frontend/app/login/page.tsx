"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { LogIn, Mail, Lock, AlertCircle, CheckCircle2, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { BASE_API_URL } from "@/utils/constants";
import { useAuth } from "@/lib/auth-context";

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

function validate(email: string, password: string): string | null {
  if (!EMAIL_REGEX.test(email)) return "Please enter a valid email address.";
  if (password.length < 7) return "Password must be at least 7 characters.";
  return null;
}

function LoginForm() {
    const router = useRouter();
    const { login } = useAuth();
    const searchParams = useSearchParams();
    const registered = searchParams.get("registered") === "true";

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
    const [isLoading, setIsLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setFieldErrors({});

        // Client-side validation
        const clientError = validate(email, password);
        if (clientError) {
          setError(clientError);
          return;
        }

        setIsLoading(true);

        try {
            const response = await fetch(`${BASE_API_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ email, password }),
            });

            if (response.ok) {
                await login();
                router.push("/");
            } else if (response.status === 401) {
                // Show the server's detailed message, or a fallback
                const data = await response.json().catch(() => ({}));
                setError(data.detail || "Invalid email or password.");
            } else if (response.status === 422) {
                const data = await response.json().catch(() => ({}));
                const msg = data.detail?.[0]?.msg || data.detail || "Validation error.";
                setError(msg);
            } else {
                const data = await response.json().catch(() => ({}));
                setError(data.detail || "Login failed. Please try again.");
            }
        } catch {
            setError("Unable to connect to the server. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-full flex-col bg-background">
            <main className="flex-1 flex items-center justify-center px-4 py-12">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                            <LogIn className="h-6 w-6 text-primary" />
                        </div>
                        <CardTitle className="text-xl">Welcome Back</CardTitle>
                        <CardDescription>
                            Sign in to your account to continue
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {registered && (
                            <Alert className="mb-6 border-emerald-500/30 bg-emerald-500/10">
                                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                <AlertDescription className="text-emerald-600 dark:text-emerald-400">
                                    Registration successful! Please log in.
                                </AlertDescription>
                            </Alert>
                        )}

                        {error && !fieldErrors.email && !fieldErrors.password && (
                            <Alert variant="destructive" className="mb-6">
                                <AlertCircle className="h-4 w-4" />
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                            <div className="flex flex-col gap-1.5">
                                <label
                                    htmlFor="login-email"
                                    className="text-xs font-semibold text-foreground"
                                >
                                    Email
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                    <Input
                                        id="login-email"
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={(e) => { setEmail(e.target.value); setFieldErrors((p) => ({ ...p, email: undefined })); }}
                                        required
                                        className="pl-9"
                                    />
                                </div>
                                {fieldErrors.email && (
                                    <p className="text-xs text-destructive">{fieldErrors.email}</p>
                                )}
                            </div>

                            <div className="flex flex-col gap-1.5">
                                <label
                                    htmlFor="login-password"
                                    className="text-xs font-semibold text-foreground"
                                >
                                    Password
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                    <Input
                                        id="login-password"
                                        type={showPassword ? "text" : "password"}
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => { setPassword(e.target.value); setFieldErrors((p) => ({ ...p, password: undefined })); }}
                                        required
                                        className="pl-9 pr-9"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                        tabIndex={-1}
                                    >
                                        {showPassword ? (
                                            <EyeOff className="h-4 w-4" />
                                        ) : (
                                            <Eye className="h-4 w-4" />
                                        )}
                                    </button>
                                </div>
                                {fieldErrors.password && (
                                    <p className="text-xs text-destructive">{fieldErrors.password}</p>
                                )}
                            </div>

                            <Button
                                type="submit"
                                disabled={isLoading}
                                className="mt-2 w-full"
                            >
                                {isLoading ? "Signing in..." : "Sign In"}
                            </Button>
                        </form>

                        <p className="mt-6 text-center text-sm text-muted-foreground">
                            Don&apos;t have an account?{" "}
                            <Link
                                href="/register"
                                className="font-medium text-primary underline-offset-4 hover:underline"
                            >
                                Register
                            </Link>
                        </p>
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}

export default function LoginPage() {
    return (
        <Suspense>
            <LoginForm />
        </Suspense>
    );
}
