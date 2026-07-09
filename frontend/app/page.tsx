"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
    const router = useRouter();

    useEffect(() => {
        const storedData = localStorage.getItem("earthquake_assessment");

        if (!storedData) {
            router.replace("/form");
            return;
        }

        try {
            JSON.parse(storedData);
        } catch {
            localStorage.removeItem("earthquake_assessment");
            router.replace("/form");
        }
    }, [router]);

    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-24"></main>
    );
}
