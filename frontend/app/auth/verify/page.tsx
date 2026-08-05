"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { BASE_API_URL } from "@/utils/constants";

function VerifyContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const type = searchParams.get("type") || "email_verify";

  // Initialize state based on presence of token to avoid synchronous setState in effect
  const initialStatus = token ? ("loading" as const) : ("error" as const);
  const initialMessage = token ? "" : "Missing verification token. The link may be invalid.";
  const [status, setStatus] = useState<"loading" | "success" | "error">(initialStatus);
  const [message, setMessage] = useState(initialMessage);

  // Guard against setting state on an unmounted component
  const mountedRef = useRef(true);
  // Guard against duplicate calls in StrictMode
  const calledRef = useRef(false);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    if (!token) {
      // token absence already handled in initial state
      return;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    const endpoint =
      type === "email_change"
        ? `${BASE_API_URL}/auth/change-email/confirm?token=${token}`
        : `${BASE_API_URL}/auth/verify/confirm?token=${token}`;

    fetch(endpoint, { credentials: "include", signal: controller.signal })
      .then(async (res) => {
        if (!mountedRef.current) return;
        const data = await res.json().catch(() => ({}));
        if (res.ok) {
          setStatus("success");
          setMessage(
            type === "email_change"
              ? "Your email has been changed successfully."
              : "Your email has been verified successfully.",
          );
        } else {
          setStatus("error");
          setMessage(
            typeof data.detail === "string"
              ? data.detail
              : "Verification failed. The link may be expired.",
          );
        }
      })
      .catch((err: Error) => {
        if (!mountedRef.current) return;
        if (err.name === "AbortError") {
          setStatus("error");
          setMessage("Request timed out. Please try again.");
        } else {
          setStatus("error");
          setMessage("Unable to connect to the server. Please try again.");
        }
      })
      .finally(() => clearTimeout(timeoutId));

    return () => {
      mountedRef.current = false;
      controller.abort();
      clearTimeout(timeoutId);
    };
  }, [token, type]);

  return (
    <div className="flex min-h-full flex-col bg-background">
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-xl">
              {status === "loading" ? "Verifying..." : status === "success" ? "Success!" : "Verification Failed"}
            </CardTitle>
            <CardDescription>
              {type === "email_change"
                ? "Email change confirmation"
                : "Email address verification"}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4 text-center">
            {status === "loading" && (
              <Loader2 className="h-10 w-10 animate-spin text-primary" />
            )}

            {status === "success" && (
              <>
                <CheckCircle2 className="h-10 w-10 text-emerald-500" />
                <Alert className="border-emerald-500/30 bg-emerald-500/10">
                  <AlertDescription className="text-emerald-600">{message}</AlertDescription>
                </Alert>
                <Link href="/login">
                  <Button>Go to Login</Button>
                </Link>
              </>
            )}

            {status === "error" && (
              <>
                <AlertCircle className="h-10 w-10 text-destructive" />
                <Alert variant="destructive">
                  <AlertDescription>{message}</AlertDescription>
                </Alert>
                <Link href="/">
                  <Button variant="outline">Go Home</Button>
                </Link>
              </>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

export default function VerifyPage() {
  return (
    <Suspense>
      <VerifyContent />
    </Suspense>
  );
}
