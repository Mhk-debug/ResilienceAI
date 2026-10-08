import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Edge gate for /dashboard, /form and /assessments.
 *
 * Intentionally a *presence + expiry* check only — the backend
 * (`get_current_user_from_cookie`) remains the source of truth for
 * signature verification. Verifying the signature here as well required
 * the frontend (JWT_SECRET) and backend (SECRET_KEY) to stay in sync;
 * any drift locked signed-in users out of /form with a redirect to
 * /login even though /api/auth/me said they were authenticated.
 */
function isExpired(token: string): boolean {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return true;
    // base64url -> base64 for atob (Edge-safe, no Buffer/dependency).
    let b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const pad = b64.length % 4;
    if (pad === 1) return true;
    if (pad > 0) b64 += "=".repeat(4 - pad);
    const payload = JSON.parse(atob(b64));
    if (typeof payload.exp !== "number") return false;
    // Small leeway so clock skew can't log a fresh login out.
    return Date.now() / 1000 > payload.exp - 30;
  } catch {
    return true;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Protect /dashboard, /form, and /assessments
  if (
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/form") ||
    pathname.startsWith("/assessments")
  ) {
    const token = request.cookies.get("access_token")?.value;

    if (!token || isExpired(token)) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/form/:path*", "/assessments/:path*"],
};