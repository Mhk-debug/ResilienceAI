# localStorage → API Migration Plan

## Current State (Full Inventory)

### 1. Files using localStorage

| File | Key | Op | Format | Purpose |
|------|-----|----|--------|---------|
| `frontend/components/local-storage-manager.tsx:12` | `latestAssessmentId` | `setItem` | UUID string | On dashboard mount, saves the current assessment ID |
| `frontend/components/local-storage-manager.tsx:15` | `assessmentHistory` | `getItem` | JSON array of UUIDs | Reads existing history to merge |
| `frontend/components/local-storage-manager.tsx:24` | `assessmentHistory` | `setItem` | JSON array (capped 8) | Prepends current ID, writes back |
| `frontend/app/page.tsx:10` | `latestAssessmentId` | `getItem` | UUID string | Home page reads it to redirect to last dashboard |
| `frontend/app/page.tsx:20` | `earthquake_assessment` | `removeItem` | (orphaned) | Cleanup of very old key during a catch block |

### 2. Orphaned / Dead Keys

- **`earthquake_assessment`** — written nowhere in current code, only cleaned up. Safe to ignore; already being removed on error path.
- **`assessmentHistory`** — **written but never read by any UI component.** No page or widget displays a history list. The only consumer is `LocalStorageManager` itself, which reads it back to deduplicate before writing. This is effectively dead data.

### 3. Data Flow

```
Home Page (/)                 Dashboard (/dashboard/[id])
    │                               │
    │ read latestAssessmentId        │ mounts <LocalStorageManager id={...}>
    │ (localStorage)                 │
    │                               ├─ setItem('latestAssessmentId', id)
    │ if exists ───→ /dashboard/X   ├─ getItem('assessmentHistory')
    │ if missing ──→ /form          ├─ prepend id, slice(0,8)
    │                               └─ setItem('assessmentHistory', [...])
```

### 4. Existing Auth Infrastructure

| Layer | File | Details |
|-------|------|---------|
| Auth middleware | `frontend/middleware.ts` | JWT cookie check; protects `/dashboard/*` and `/form/*` |
| Auth context | `frontend/lib/auth-context.tsx` | `AuthProvider` → `GET /auth/me`, exposes `user`, `isAuthenticated`, `isLoading` |
| SSE cookie forward | `frontend/app/api/sse/assessment/process/route.ts` | Forwards `access_token` cookie to backend |
| Backend auth dep | `backend/services/auth.py` | `get_current_user_from_cookie()` — FastAPI dependency |
| Assessment ownership | `backend/routes/assessment.py` | `GET /assessment/{id}` checks `assessment.user_id == current_user.id`, returns 403 otherwise |
| FK relationship | `backend/database/models.py` | `Assessment.user_id` FK → `users.id`, `owner` relationship back_populates |

---

## Migration Plan

### Phase 1 — Add Backend Endpoint: `GET /assessments` (List User's Assessments)

**File:** `backend/routes/assessment.py`

Add a new route that queries assessments for the current user, ordered by `created_at DESC`:

```python
@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List all assessments for the authenticated user",
)
def list_user_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    limit: int = 20,
    offset: int = 0,
):
    assessments = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return assessments
```

Consider returning a lightweight summary (id, created_at, place_name, resilience_score, hazard_score, hazard_level) rather than the full JSONB blobs, to keep list queries fast.

### Phase 2 — Replace Home Page Redirect Logic

**File:** `frontend/app/page.tsx`

**Current behavior:** Reads `latestAssessmentId` from localStorage; redirects to `/dashboard/{id}` if found, else `/form`.

**Target behavior:** Three-tier redirect:

1. **If authenticated** (use `useAuth()` from the auth context):
   - Fetch `GET /assessments?limit=1` from the API
   - If the user has assessments → redirect to `/dashboard/{latest_id}`
   - If the user has no assessments → redirect to `/form`
2. **If not authenticated** (or still loading):
   - Fall back to localStorage `latestAssessmentId` (preserves existing behavior for anonymous users / edge cases)
   - If no localStorage → redirect to `/form`

**Why blend both:** After login (from `/login` or `/register`), the `useAuth()` context will know `isAuthenticated=true`, so the API path is taken. For users who land on `/` without a session token, localStorage still works as today.

**What to change:**
```tsx
"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { BASE_API_URL } from "@/utils/constants";

export default function Home() {
    const router = useRouter();
    const { user, isAuthenticated, isLoading } = useAuth();

    useEffect(() => {
        if (isLoading) return; // wait for auth check

        if (isAuthenticated && user) {
            // Tier 1: logged-in user → fetch from API
            fetch(`${BASE_API_URL}/assessment?limit=1`, { credentials: "include" })
                .then((res) => res.ok ? res.json() : Promise.reject())
                .then((assessments) => {
                    if (Array.isArray(assessments) && assessments.length > 0) {
                        router.replace(`/dashboard/${assessments[0].id}`);
                    } else {
                        router.replace("/form");
                    }
                })
                .catch(() => {
                    router.replace("/form");
                });
        } else {
            // Tier 2: anonymous → fall back to localStorage
            try {
                const latestId = localStorage.getItem("latestAssessmentId");
                if (latestId) {
                    router.replace(`/dashboard/${latestId}`);
                } else {
                    router.replace("/form");
                }
            } catch {
                router.replace("/form");
            }
        }
    }, [router, user, isAuthenticated, isLoading]);

    return ( /* loader spinner (unchanged) */ );
}
```

### Phase 3 — Keep `LocalStorageManager` as Optional Fast-Cache; Add API Sync

**File:** `frontend/components/local-storage-manager.tsx`

**Keep as-is for caching.** The localStorage write is harmless and provides a fast redirect path for the small window between auth check completion and API response on subsequent visits. Do NOT remove it — it becomes a non-authoritative fast cache.

**Optional enhancement:** Add a check to ensure the cached ID actually exists on the server before redirecting, but this is overengineering unless stale redirects are observed.

### Phase 4 — Remove Dead Code: `assessmentHistory`

**File:** `frontend/components/local-storage-manager.tsx`

**Remove lines 14-25** (the `assessmentHistory` read-merge-write block). Key is never consumed by any component. Any future assessment-list UI should be API-driven via the new `GET /assessments` endpoint, not localStorage.

Updated component:
```tsx
import { useEffect } from 'react';

interface LocalStorageManagerProps {
  id: string;
}

export function LocalStorageManager({ id }: LocalStorageManagerProps) {
  useEffect(() => {
    if (!id) return;
    try {
      localStorage.setItem('latestAssessmentId', id);
    } catch (e) {
      console.warn('Local storage not accessible: ', e);
    }
  }, [id]);

  return null;
}
```

### Phase 5 — Replace Dead Redirect in Catch Block

**File:** `frontend/app/page.tsx`

The `catch` block on line 18-22 removes `earthquake_assessment` (ancient key, written nowhere). This is a no-op cleanup and can be removed entirely. Replace with a clean `router.replace("/form")`.

### Phase 6 — Migration Path for Existing localStorage Data

Calculate a simple migration value:

| Scenario | Current behavior | After migration |
|----------|-----------------|-----------------|
| Registered user, has assessments in DB | Redirects to last local ID (may 403 if not theirs) | Redirects to API result for *their* assessments |
| Registered user, cleared localStorage | Redirects to `/form` | Redirects to `/form` (but could instead show "no assessments" if API returns empty) |
| Anonymous user (no cookie), has local data | Redirects to `/dashboard/{id}` | Redirects to `/dashboard/{id}` via localStorage fallback (same as before if middleware doesn't block — but it does: `/dashboard` requires auth) |
| Anonymous user, no local data | Redirects to `/form` → then middleware redirects to `/login` | Same |

**Note:** The middleware already protects `/dashboard/*` and `/form/*` with JWT cookie verification, so anonymous users are always redirected to `/login` regardless. The localStorage fallback for anonymous users in the home page redirect is effectively unreachable for dashboard routes — they'll hit the middleware first. This is fine; keep the fallback for resilience (e.g., if middleware rules change).

### Phase 7 — (Optional) Add Assessment History UI

If you want a landing page between login and the form, add a history page at `/history` or modify `/` to render an assessment list instead of immediately redirecting:

```tsx
// Pseudocode for a future assessment list page
const { user, isAuthenticated } = useAuth();
const [assessments, setAssessments] = useState([]);

useEffect(() => {
    if (isAuthenticated) {
        fetch(`${BASE_API_URL}/assessment?limit=50`, { credentials: "include" })
            .then(r => r.json())
            .then(setAssessments);
    }
}, [isAuthenticated]);
```

This is **not required** for the migration — the immediate redirect is fine — but it's a natural UX improvement once the API endpoint exists.

---

## Summary of Changes

| # | File | Action | Reason |
|---|------|--------|--------|
| 1 | `backend/routes/assessment.py` | **Add** `GET /assessments` (list by user) | No server-side history exists today |
| 2 | `frontend/app/page.tsx` | **Rewrite** redirect logic | Use API when authenticated, localStorage fallback for anonymous |
| 3 | `frontend/components/local-storage-manager.tsx` | **Simplify** — remove `assessmentHistory` block | Dead code (written, never read by UI) |
| 4 | `frontend/app/page.tsx` | **Remove** `earthquake_assessment` catch cleanup | Orphaned cleanup of nonexistent key |

### What stays the same

- `localStorage.setItem('latestAssessmentId', ...)` in `LocalStorageManager` — kept as fast client-side cache
- The auth middleware, auth context, SSE proxy, and backend assessment ownership checks — all already correct
- The form page, dashboard components, login/register — no localStorage changes needed

### Migration safety

- **Existing localStorage data is never lost** — only the `assessmentHistory` key stops being written. `latestAssessmentId` continues to be written on every dashboard visit.
- **The home page for authenticated users switches from localStorage-first to API-first.** If the API is down, the catch block redirects to `/form` (same as today's fallback).
- **The `GET /assessments` endpoint is the only new backend code.** Everything else is frontend-only reconfiguration.
