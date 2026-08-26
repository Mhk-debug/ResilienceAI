import type { Metadata } from "next";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";
import Header from "@/components/header";
import { AuthProvider } from "@/lib/auth-context";

export const metadata: Metadata = {
    title: "ResilienceAI",
    description: "Earthquake Resilience Assessment Platform",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" className="h-full antialiased">
            <TooltipProvider>
                <AuthProvider>
                    <body className="min-h-full flex flex-col font-mono">
                        <Header />
                        {children}
                    </body>
                </AuthProvider>
            </TooltipProvider>
        </html>
    );
}
