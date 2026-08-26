import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { jwtVerify } from "jose";

const SECRET_KEY = new TextEncoder().encode(
  process.env.JWT_SECRET || "super-secret-key"
);

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Protect /dashboard, /form, and /assessments
  if (
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/form") ||
    pathname.startsWith("/assessments")
  ) {
    const token = request.cookies.get("access_token")?.value;

    if (!token) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    try {
      // Verify the JWT: checks signature, expiry, and that it was signed by our server
      await jwtVerify(token, SECRET_KEY);
      return NextResponse.next();
    } catch {
      // Token is invalid, tampered, expired, or not signed by our server
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/form/:path*", "/assessments/:path*"],
};