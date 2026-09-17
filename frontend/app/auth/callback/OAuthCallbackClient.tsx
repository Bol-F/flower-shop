"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  OfflineError,
  completeOAuth,
  completeOAuthLink,
  type OAuthProvider,
} from "@/lib/api";
import { useStore } from "@/lib/store";

const fallbackNextPath = "/profile";
const unsafePathCharacters = /[\u0000-\u001f\u007f\\]/u;
const unsafeEncodedPathCharacters = /%(?:2f|5c|0[0-9a-f]|1[0-9a-f]|7f)/iu;
const providerLabels: Record<OAuthProvider, string> = {
  google: "Google",
  github: "GitHub",
  microsoft: "Microsoft",
};

function isOAuthProvider(value: string): value is OAuthProvider {
  return value === "google" || value === "github" || value === "microsoft";
}

function safeNextPath(value: string) {
  const encodedPath = value.split(/[?#]/u, 1)[0];
  if (
    !value.startsWith("/") ||
    value.startsWith("//") ||
    unsafePathCharacters.test(value) ||
    unsafeEncodedPathCharacters.test(encodedPath)
  ) {
    return fallbackNextPath;
  }

  try {
    const destination = new URL(value, window.location.origin);
    if (
      destination.origin !== window.location.origin ||
      destination.pathname.startsWith("//") ||
      destination.username ||
      destination.password
    ) {
      return fallbackNextPath;
    }
    return `${destination.pathname}${destination.search}${destination.hash}`;
  } catch {
    return fallbackNextPath;
  }
}

interface CallbackFailure {
  message: string;
  isLink: boolean;
  canRetry: boolean;
}

interface CallbackCredential {
  code: string;
  isLink: boolean;
  next: string;
  provider: string;
}

function retryableFailure(reason: unknown) {
  return (
    reason instanceof OfflineError ||
    (reason instanceof ApiError && (reason.status === 429 || reason.status >= 500))
  );
}

export default function OAuthCallbackClient({
  error,
  flow,
  message,
}: {
  error: string;
  flow: string;
  message: string;
}) {
  const router = useRouter();
  const { setUser, setName, showToast } = useStore();
  const initialized = useRef(false);
  const credential = useRef<CallbackCredential | null>(null);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const [failure, setFailure] = useState<CallbackFailure | null>(
    error
      ? {
          message: message || "The connection was not completed.",
          isLink: flow === "link",
          canRetry: false,
        }
      : null,
  );

  useEffect(() => {
    let failureTimer: number | undefined;
    if (!initialized.current) {
      initialized.current = true;
      const fragment = new URLSearchParams(window.location.hash.slice(1));
      const loginCode = (fragment.get("code") || "").trim();
      const accountLinkCode = (fragment.get("link_code") || "").trim();

      // Remove one-time credentials before any network request, navigation, or error rendering.
      window.history.replaceState(null, "", window.location.pathname);

      if (error) return;
      if ((!loginCode && !accountLinkCode) || (loginCode && accountLinkCode)) {
        failureTimer = window.setTimeout(() => {
          setFailure({
            message: "The connection response did not include one usable code.",
            isLink: Boolean(accountLinkCode) || flow === "link",
            canRetry: false,
          });
        }, 0);
        return () => window.clearTimeout(failureTimer);
      }
      credential.current = {
        code: accountLinkCode || loginCode,
        isLink: Boolean(accountLinkCode),
        next: fragment.get("next") || fallbackNextPath,
        provider: fragment.get("provider") || "",
      };
    }

    const pending = credential.current;
    if (!pending || error) return;
    let active = true;
    const destination = safeNextPath(pending.next);
    if (pending.isLink) {
      void completeOAuthLink(pending.code)
        .then((user) => {
          if (!active) return;
          setUser(user);
          setName(user.username);
          const label = isOAuthProvider(pending.provider)
            ? providerLabels[pending.provider]
            : "Account";
          showToast(`${label} is now connected.`);
          router.replace(destination);
        })
        .catch((reason: unknown) => {
          if (!active) return;
          setFailure({
            message:
              reason instanceof Error
                ? reason.message
                : "This account connection is invalid or expired.",
            isLink: true,
            canRetry: retryableFailure(reason),
          });
        });
    } else {
      void completeOAuth(pending.code)
        .then((user) => {
          if (!active) return;
          setUser(user);
          setName(user.username);
          showToast(`Welcome, ${user.username}`);
          router.replace(destination);
        })
        .catch((reason: unknown) => {
          if (!active) return;
          setFailure({
            message:
              reason instanceof Error ? reason.message : "This sign-in link is invalid or expired.",
            isLink: false,
            canRetry: retryableFailure(reason),
          });
        });
    }
    return () => {
      active = false;
      if (failureTimer !== undefined) window.clearTimeout(failureTimer);
    };
  }, [error, flow, retryAttempt, router, setName, setUser, showToast]);

  if (failure) {
    return (
      <section className="mx-auto max-w-lg rounded-[2rem] border border-line bg-white p-7 text-center shadow-lift">
        <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-berrysoft text-2xl">
          ×
        </div>
        <h1 className="mt-4 font-display text-3xl font-extrabold text-ink">
          {failure.isLink ? "Connection paused" : "Sign-in paused"}
        </h1>
        <p role="alert" className="mt-3 text-sm font-semibold leading-6 text-stone">
          {failure.message}
        </p>
        {failure.canRetry && (
          <button
            type="button"
            onClick={() => {
              setFailure(null);
              setRetryAttempt((attempt) => attempt + 1);
            }}
            className="mt-6 inline-flex rounded-full bg-blossomdeep px-6 py-3 text-sm font-extrabold text-white shadow-glow"
          >
            Try exchange again
          </button>
        )}
        <Link
          href={failure.isLink ? "/profile" : "/profile?mode=login"}
          className="mt-6 inline-flex rounded-full border border-line bg-white px-6 py-3 text-sm font-extrabold text-ink"
        >
          {failure.isLink ? "Return to profile" : "Return to sign in"}
        </Link>
      </section>
    );
  }

  return (
    <section
      className="mx-auto max-w-lg rounded-[2rem] border border-line bg-white p-7 text-center shadow-lift"
      aria-live="polite"
    >
      <div className="mx-auto size-12 animate-spin rounded-full border-4 border-blush border-t-blossomdeep" />
      <h1 className="mt-5 font-display text-3xl font-extrabold text-ink">
        Finishing secure connection
      </h1>
      <p className="mt-2 text-sm font-semibold text-stone">
        Securely exchanging your one-time code…
      </p>
    </section>
  );
}
