import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";
import Header from "@/components/header";
import { AuthProvider } from "@/lib/auth-context";

const geistSans = Geist({
    variable: "--font-geist-sans",
    subsets: ["latin"],
});

const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});

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
        <html
            lang="en"
            className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
        >
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
