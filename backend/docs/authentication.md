# Authentication Foundation

This document outlines the core authentication infrastructure for ResilienceAI.

## Overview
The application uses JSON Web Tokens (JWT) for session management, with tokens stored in secure, HTTP-only cookies to mitigate CSRF/XSS risks.

## User Model
The `User` model (`backend/database/models.py`) stores user credentials:
- `id`: UUID (Primary Key)
- `email`: String (Unique, Indexed)
- `hashed_password`: String (BCrypt hash)
- `is_active`: Boolean
- `created_at`: DateTime

## Auth Service
`backend/services/auth.py` handles:
- Password hashing (using `passlib` with `bcrypt`)
- JWT creation (`python-jose`)
- JWT validation
- Cookie management

## API Routes
- `POST /auth/register`: Creates a new user.
- `POST /auth/login`: Authenticates, sets `access_token` cookie.
- `POST /auth/logout`: Clears the cookie.
- `GET /auth/me`: Returns current user info.

## Frontend
- `frontend/lib/auth-context.tsx`: Provides React auth state.
- `frontend/middleware.ts`: Presence + expiry gate on `/dashboard`, `/form`, and `/assessments` (redirects to `/login` when the `access_token` cookie is missing or expired). JWT signature verification happens on the backend via `get_current_user_from_cookie()` on every API call.
