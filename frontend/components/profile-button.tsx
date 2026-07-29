"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronDown,
  KeyRound,
  Mail,
  ShieldCheck,
  LogOut,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth-context";
import { BASE_API_URL } from "@/utils/constants";
import {
  ChangePasswordModal,
  ChangeEmailModal,
  VerifyEmailModal,
} from "./profile-modals";

function ProfileButton() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  const [showChangePassword, setShowChangePassword] = useState(false);
  const [showChangeEmail, setShowChangeEmail] = useState(false);
  const [showVerifyEmail, setShowVerifyEmail] = useState(false);

  const handleLogout = async () => {
    try {
      await fetch(`${BASE_API_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch {
      // Logout even if server is unreachable
    }
    logout();
    router.push("/login");
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 animate-pulse rounded-full bg-primary-foreground/10" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null; // parent header shows Login/Register buttons instead
  }

  const initial = user.email.charAt(0).toUpperCase();

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger className="flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm font-medium text-primary-foreground/70 hover:text-primary-foreground hover:bg-primary-foreground/10 transition-colors outline-none">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-foreground/15 text-xs font-bold text-primary-foreground">
            {initial}
          </span>
          <ChevronDown className="h-3.5 w-3.5" />
        </DropdownMenuTrigger>

        <DropdownMenuContent>
          {/* Email header */}
          <div className="flex flex-col gap-0.5 px-3 py-2">
            <span className="truncate text-sm font-medium text-foreground">
              {user.email}
            </span>
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              {user.email_verified ? (
                <>
                  <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                  Verified
                </>
              ) : (
                <>
                  <AlertTriangle className="h-3 w-3 text-amber-500" />
                  Not verified
                </>
              )}
            </span>
          </div>

          <DropdownMenuSeparator />

          <DropdownMenuItem onClick={() => setShowChangePassword(true)}>
            <KeyRound className="h-4 w-4 text-muted-foreground" />
            Change Password
          </DropdownMenuItem>

          <DropdownMenuItem onClick={() => setShowChangeEmail(true)}>
            <Mail className="h-4 w-4 text-muted-foreground" />
            Change Email
          </DropdownMenuItem>

          {!user.email_verified && (
            <DropdownMenuItem onClick={() => setShowVerifyEmail(true)}>
              <ShieldCheck className="h-4 w-4 text-muted-foreground" />
              Verify Email
            </DropdownMenuItem>
          )}

          <DropdownMenuSeparator />

          <DropdownMenuItem onClick={handleLogout}>
            <LogOut className="h-4 w-4 text-muted-foreground" />
            <span className="text-destructive">Logout</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Modals */}
      <ChangePasswordModal
        open={showChangePassword}
        onOpenChange={setShowChangePassword}
      />
      <ChangeEmailModal
        open={showChangeEmail}
        onOpenChange={setShowChangeEmail}
      />
      <VerifyEmailModal
        open={showVerifyEmail}
        onOpenChange={setShowVerifyEmail}
      />
    </>
  );
}

export default ProfileButton;
