# Profile Button Feature — Full Architecture Plan

## Goal

Merge the current email display + Logout button (right side of header) into a single **Profile button** that opens a dropdown with: Logout, Change Password, Change Email, Verify Email. Add email verification to the user model.

---

## Part 1: Database — User Model Changes

**File:** `backend/database/models.py`

Add these columns to the `User` model:

| Column | Type | Nullable | Default | Purpose |
|---|---|---|---|---|
| `email_verified` | `Boolean` | No | `False` | Whether the user has verified their email |
| `verification_token` | `String` | Yes | `None` | Email verification token (sent at registration or resend) |
| `verification_token_expires` | `DateTime(tz)` | Yes | `None` | Expiry for verification token (24h) |
| `password_reset_token` | `String` | Yes | `None` | Token for password reset |
| `password_reset_token_expires` | `DateTime(tz)` | Yes | `None` | Expiry for password reset token (1h) |
| `new_email` | `String` | Yes | `None` | Pending email change (stored until verified) |
| `email_change_token` | `String` | Yes | `None` | Verification token for email change |
| `email_change_token_expires` | `DateTime(tz)` | Yes | `None` | Expiry for email change token (1h) |
| `password_changed_at` | `DateTime(tz)` | Yes | `None` | Timestamp of last password change (audit) |

---

## Part 2: Backend — Auth Service Changes

### 2a. New service functions (`backend/services/auth.py`)

1. **`generate_token() -> str`**  
   Uses `secrets.token_urlsafe(32)` for secure random tokens.

2. **`send_verification_email(email: str, token: str)`**  
   New **`EmailService`** class using `smtplib` (SMTP).  
   Config via env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`.  
   Sends HTML email with verification link:  
   `{FRONTEND_URL}/auth/verify?token={token}`  
   Falls back gracefully — logs the token to console if SMTP is not configured (dev mode).

3. **`verify_token(user: User, token_field: str, expires_field: str, token: str) -> bool`**  
   Generic token verification helper. Checks token match and expiry.

### 2b. New route schemas (`backend/routes/auth.py`)

```python
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ChangeEmailRequest(BaseModel):
    new_email: str
    current_password: str

class VerifyEmailRequest(BaseModel):
    token: str

class SendVerificationEmail(BaseModel):
    email: str   # optional — defaults to current user's email
```

### 2c. New auth routes

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/auth/change-password` | Yes | Verify current password, hash + save new one |
| `POST` | `/auth/change-email/initiate` | Yes | Save `new_email`, generate `email_change_token`, send verification to new email |
| `GET` | `/auth/change-email/confirm` | No | Accept `?token=xxx`, swap email, clear token |
| `POST` | `/auth/verify/send` | Yes | Generate + send verification token via email |
| `GET` | `/auth/verify/confirm` | No | Accept `?token=xxx`, set `email_verified=True` |
| `GET` | `/auth/me` | Yes | **Update** response to include `email_verified` |

### 2d. Updated `/auth/me` response

```json
{
  "email": "user@example.com",
  "id": "uuid",
  "email_verified": true
}
```

---

## Part 3: Backend — New File Structure

```
backend/
  services/
    auth.py          ← Add token generation, email service, token verification
    email_service.py ← NEW: EmailService class (SMTP)
  routes/
    auth.py          ← Add new route endpoints + Pydantic schemas
  database/
    models.py        ← Add new User columns (see Part 1)
```

Actually simpler to keep email service in `services/auth.py` since it's small — the `EmailService` can be a small helper class at the bottom of the file.

---

## Part 4: Frontend — New UI Components

### 4a. DropdownMenu component (new shadcn/ui component)

We need a `<DropdownMenu>` component. Since the project uses `@base-ui/react` (shadcn's "base-nova" style), the dropdown menu will use `@base-ui/react/menu`.

**File:** `components/ui/dropdown-menu.tsx`

This wraps `@base-ui/react/menu` primitives with the project's styling conventions. Provides:
- `DropdownMenu` (root)
- `DropdownMenuTrigger`
- `DropdownMenuContent`
- `DropdownMenuItem`
- `DropdownMenuSeparator`

### 4b. ProfileButton component (new)

**File:** `components/profile-button.tsx`

Renders a trigger button showing the user's **first email letter as avatar** + a chevron-down icon. On click, opens a dropdown with:

```
┌─────────────────────────────┐
│  user@example.com           │
│  ─────────────────────────  │
│  🟢 Change Password         │
│  ✉️ Change Email            │
│  🔒 Verify Email  [Unver.]  │  ← hides if already verified
│  ─────────────────────────  │
│  🚪 Logout                  │
└─────────────────────────────┘
```

Each item (except Logout) opens a modal dialog.

### 4c. Dialog component (new or existing)

The project doesn't have a Dialog component yet. We'll create one using `@base-ui/react/dialog`:

**File:** `components/ui/dialog.tsx`

### 4d. Modal dialogs

**File:** `components/profile-modals.tsx`

Contains:
- `ChangePasswordModal` — Current password, new password, confirm new password, submit, feedback
- `ChangeEmailModal` — New email, current password (for re-auth), submit, feedback  
- `VerifyEmailModal` — Shows "Send verification email" button, confirms sent, provides link to resend

### 4e. Updated Header

**File:** `components/header.tsx`

Replace the email span + logout button with `<ProfileButton />` when authenticated.  
When not authenticated — keep Login/Register buttons as-is.

### 4f. Updated AuthContext

**File:** `lib/auth-context.tsx`

- Update the `User` interface to include `email_verified: boolean`
- The `/auth/me` response now includes `email_verified`, so `checkAuth()` picks it up automatically
- Add a `refreshUser()` method that re-fetches `/auth/me`
- Add optional callbacks after password/email changes to refresh user state

### 4g: Verify email page (optional fallback)

**File:** `app/auth/verify/page.tsx` (new)

If the user clicks the verification link in their email and the app isn't open, this page handles the token on load:
- Reads `?token=xxx` from URL
- Calls `GET /auth/verify/confirm?token=xxx`
- Shows success/error message with a link to login

### 4h: Middleware update (no changes needed)

The existing middleware at `frontend/middleware.ts` already protects `/dashboard` and `/form`. No changes needed for the profile feature.

---

## Part 5: Frontend Flow Diagrams

### 5a. Header Changes (visual layout)

```
BEFORE (authenticated):
┌──────────────────────────────────────────────────┐
│ 🌀 Earthquake Risk Assessment AI    user@ex... 🚪 │
│     codeTrio · STIMU                              │
└──────────────────────────────────────────────────┘

AFTER (authenticated):
┌──────────────────────────────────────────────────┐
│ 🌀 Earthquake Risk Assessment AI         [ U ▼ ] │
│     codeTrio · STIMU                              │
└──────────────────────────────────────────────────┘
```

### 5b. Change Password Flow

```
User clicks "Change Password"
  → Modal opens: [Current Password] [New Password] [Confirm New] [Save]
  → POST /auth/change-password { current_password, new_password }
  → Success: modal closes, toast "Password changed"
  → Error: inline error in modal
```

### 5c. Change Email Flow

```
User clicks "Change Email"
  → Modal opens: [New Email] [Current Password] [Send Verification]  
  → POST /auth/change-email/initiate { new_email, current_password }
  → Success: "Verification sent to {new_email}. Check your inbox."
  → User clicks link in email → GET /auth/change-email/confirm?token=xxx
  → Page shows "Email changed successfully"
  → AuthContext refreshes with new email
```

### 5d. Verify Email Flow

```
User clicks "Verify Email"
  → Modal opens: "Your email is not yet verified. Send verification?"
  → POST /auth/verify/send
  → Success: "Verification email sent to {email}"
  → User clicks link in email → GET /auth/verify/confirm?token=xxx  
  → Page shows "Email verified successfully"
  → AuthContext refreshes with email_verified=true
```

### 5e. Registration Enhancement

On registration (`POST /auth/register`), optionally send verification email automatically so users get a head start on verification. This is a nice-to-have, not required.

---

## Part 6: Implementation Order & File Checklist

### Step 1: Backend model migration
- [ ] Edit `backend/database/models.py` — add new columns to User
- [ ] Run migration (could be `scripts/reset_db.py` for dev, or alembic for prod)

### Step 2: Backend auth service
- [ ] Edit `backend/services/auth.py` — add token generation, EmailService, verify helpers

### Step 3: Backend auth routes
- [ ] Edit `backend/routes/auth.py` — add new Pydantic schemas + 5 new endpoint handlers
- [ ] Update `/auth/me` to return `email_verified`

### Step 4: Frontend UI components
- [ ] Create `components/ui/dropdown-menu.tsx`
- [ ] Create `components/ui/dialog.tsx`
- [ ] Create `components/profile-button.tsx`
- [ ] Create `components/profile-modals.tsx`

### Step 5: Frontend auth context
- [ ] Edit `lib/auth-context.tsx` — add `email_verified` and `refreshUser()`

### Step 6: Frontend header
- [ ] Edit `components/header.tsx` — use ProfileButton instead of email+logout

### Step 7: Fallback verify page
- [ ] Create `app/auth/verify/page.tsx`

---

## Part 7: Config / Env Changes

**File:** `backend/.env` (add these — example values for dev):

```env
# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=ResilienceAI <noreply@resilienceai.app>
FRONTEND_URL=http://localhost:3000
```

If SMTP is not configured, the `EmailService` logs the verification link to console for local development — the feature works without email config, just with console-based tokens.

---

## Design Decisions

1. **Dialogs vs separate pages** — Dialogs chosen because they keep the user in context, match modern SaaS patterns (GitHub, Vercel), and avoid cluttering the route table.
2. **Email service — SMTP** — Lightweight, no external API dependency. Falls back to console logging in dev.
3. **Token-based verification** — Simple token in URL works without OAuth or third-party services.
4. **Re-auth on email change** — Requires current password to prevent account takeover.
5. **Single profile button** — Uses @base-ui/react Menu + Dialog primitives, consistent with existing shadcn/ui "base-nova" setup.

---

## File Changes Summary

| File | Action |
|---|---|
| `backend/database/models.py` | Edit — add 8 new columns |
| `backend/services/auth.py` | Edit — add token helpers, EmailService |
| `backend/routes/auth.py` | Edit — add new endpoints + schemas |
| `backend/.env` | Edit — add SMTP config vars |
| `frontend/components/ui/dropdown-menu.tsx` | **Create** |
| `frontend/components/ui/dialog.tsx` | **Create** |
| `frontend/components/profile-button.tsx` | **Create** |
| `frontend/components/profile-modals.tsx` | **Create** |
| `frontend/components/header.tsx` | Edit — use ProfileButton |
| `frontend/lib/auth-context.tsx` | Edit — add email_verified |
| `frontend/app/auth/verify/page.tsx` | **Create** |
