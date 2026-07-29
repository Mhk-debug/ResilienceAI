"use client";

import { useState } from "react";
import {
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogClose,
} from "@/components/ui/dialog";
import { useAuth } from "@/lib/auth-context";
import { BASE_API_URL } from "@/utils/constants";

// ---------------------------------------------------------------------------
// Error parsing helper (handles both string and array-shaped Pydantic errors)
// ---------------------------------------------------------------------------

function parseError(data: unknown): string {
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    const detail = (data as Record<string, unknown>).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (first && typeof first === "object") {
        const msg = (first as Record<string, unknown>).msg;
        if (typeof msg === "string") return msg;
      }
      return String(detail[0]);
    }
  }
  return "An unexpected error occurred.";
}

// ---------------------------------------------------------------------------
// Change Password Modal
// ---------------------------------------------------------------------------

export function ChangePasswordModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { refreshUser } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPassword.length < 7) {
      setError("New password must be at least 7 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (currentPassword === newPassword) {
      setError("New password must be different from your current password.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch(`${BASE_API_URL}/auth/change-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setSuccess("Password changed successfully.");
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        await refreshUser();
        setTimeout(() => onOpenChange(false), 1200);
      } else if (res.status === 422) {
        setError(parseError(data));
      } else {
        setError(parseError(data));
      }
    } catch {
      setError("Unable to connect to server. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title="Change Password">
        <DialogDescription>
          Enter your current password and a new one.
        </DialogDescription>

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {success && (
          <Alert className="mb-4 border-emerald-500/30 bg-emerald-500/10">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <AlertDescription className="text-emerald-600">
              {success}
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="mb-1 block text-xs font-semibold text-foreground">
              Current Password
            </label>
            <Input
              type={showPw ? "text" : "password"}
              placeholder="••••••••"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-foreground">
              New Password
            </label>
            <Input
              type={showPw ? "text" : "password"}
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={7}
              disabled={isLoading}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-foreground">
              Confirm New Password
            </label>
            <Input
              type={showPw ? "text" : "password"}
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={7}
              disabled={isLoading}
            />
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowPw(!showPw)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              {showPw ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
              <span className="ml-1">{showPw ? "Hide" : "Show"} passwords</span>
            </button>
          </div>
          <div className="mt-2 flex justify-end gap-2">
            <DialogClose>
              <Button type="button" variant="outline" size="sm" disabled={isLoading}>
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" size="sm" disabled={isLoading}>
              {isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              {isLoading ? "Saving..." : "Save"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Change Email Modal
// ---------------------------------------------------------------------------

export function ChangeEmailModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { refreshUser } = useAuth();
  const [newEmail, setNewEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!EMAIL_REGEX.test(newEmail)) {
      setError("Please enter a valid email address.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch(`${BASE_API_URL}/auth/change-email/initiate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ new_email: newEmail, current_password: currentPassword }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setSuccess(data.message || "Verification email sent.");
        setNewEmail("");
        setCurrentPassword("");
        await refreshUser();
      } else {
        setError(parseError(data));
      }
    } catch {
      setError("Unable to connect to server. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title="Change Email">
        <DialogDescription>
          Enter your new email and current password. A verification link will be sent to the new address.
        </DialogDescription>

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {success && (
          <Alert className="mb-4 border-emerald-500/30 bg-emerald-500/10">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <AlertDescription className="text-emerald-600">
              {success}
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="mb-1 block text-xs font-semibold text-foreground">
              New Email
            </label>
            <Input
              type="email"
              placeholder="new@example.com"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold text-foreground">
              Current Password
            </label>
            <Input
              type="password"
              placeholder="••••••••"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          <div className="mt-2 flex justify-end gap-2">
            <DialogClose>
              <Button type="button" variant="outline" size="sm" disabled={isLoading}>
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" size="sm" disabled={isLoading}>
              {isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              {isLoading ? "Sending..." : "Send Verification"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Verify Email Modal
// ---------------------------------------------------------------------------

export function VerifyEmailModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { user, refreshUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    setError(null);
    setSuccess(null);
    setIsLoading(true);
    try {
      const res = await fetch(`${BASE_API_URL}/auth/verify/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({}),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setSuccess(data.message || "Verification email sent.");
        await refreshUser();
      } else {
        setError(parseError(data));
      }
    } catch {
      setError("Unable to connect to server. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title="Verify Email">
        <DialogDescription>
          {user?.email_verified
            ? "Your email is already verified."
            : `Send a verification email to ${user?.email}?`}
        </DialogDescription>

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {success && (
          <Alert className="mb-4 border-emerald-500/30 bg-emerald-500/10">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <AlertDescription className="text-emerald-600">
              {success}
            </AlertDescription>
          </Alert>
        )}

        <div className="mt-2 flex justify-end gap-2">
          <DialogClose>
            <Button type="button" variant="outline" size="sm">
              Close
            </Button>
          </DialogClose>
          {!user?.email_verified && (
            <Button
              type="button"
              size="sm"
              disabled={isLoading}
              onClick={handleSend}
            >
              {isLoading ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <ShieldCheck className="h-3.5 w-3.5" />
              )}
              {isLoading ? "Sending..." : "Send Verification"}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
