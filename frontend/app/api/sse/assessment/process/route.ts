import { NextRequest } from "next/server";

/**
 * SSE streaming proxy for /api/assessment/process.
 *
 * Next.js built-in rewrites buffer the entire response body, which breaks
 * Server-Sent Events. This Route Handler manually pipes the SSE stream
 * from the FastAPI backend to the client chunk-by-chunk, while forwarding
 * the JWT access_token cookie for authentication.
 */
export async function POST(request: NextRequest) {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

    // Forward the JWT cookie to the backend
    const token = request.cookies.get("access_token")?.value;

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };

    if (token) {
        headers["Cookie"] = `access_token=${token}`;
    }

    const body = await request.json();

    const backendResponse = await fetch(
        `${backendUrl}/assessment/process`,
        {
            method: "POST",
            headers,
            body: JSON.stringify(body),
        },
    );

    // If the backend returns an error (e.g. 401), forward it
    if (!backendResponse.ok) {
        const errorBody = await backendResponse.text();
        return new Response(errorBody, {
            status: backendResponse.status,
            headers: {
                "Content-Type": "application/json",
            },
        });
    }

    // Stream the SSE response back to the client
    return new Response(backendResponse.body, {
        status: 200,
        headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    });
}