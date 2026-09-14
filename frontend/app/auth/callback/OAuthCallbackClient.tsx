"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { completeOAuth, completeOAuthLink, type OAuthProvider } from "@/lib/api";
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
  if (
    !value.startsWith("/") ||
    value.startsWith("//") ||
    unsafePathCharacters.test(value) ||
    unsafeEncodedPathCharacters.test(value)
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
}

export default function OAuthCallbackClient({
  code,
  linkCode,
  error,
  flow,
  message,
  next,
  provider,
}: {
  code: string;
  linkCode: string;
  error: string;
  flow: string;
  message: string;
  next: string;
  provider: string;
}) {
  const router = useRouter();
  const { setUser, setName, showToast } = useStore();
  const started = useRef(false);
  const [failure, setFailure] = useState<CallbackFailure | null>(
    error
      ? {
          message: message || "The connection was not completed.",
          isLink: flow === "link",
        }
      : null,
  );

  useEffect(() => {
    if (started.current) return;

    const fragment = new URLSearchParams(window.location.hash.slice(1));
    const hasFragmentCredential = fragment.has("code") || fragment.has("link_code");
    const loginCode = (fragment.get("code") || (hasFragmentCredential ? "" : code)).trim();
    const accountLinkCode = (
      fragment.get("link_code") || (hasFragmentCredential ? "" : linkCode)
    ).trim();
    const requestedNext = fragment.get("next") || next;
    const callbackProvider = fragment.get("provider") || provider;

    // Remove one-time credentials before any network request, navigation, or error rendering.
    window.history.replaceState(null, "", window.location.pathname);

    if (error) {
      started.current = true;
      return;
    }
    if ((!loginCode && !accountLinkCode) || (loginCode && accountLinkCode)) {
      const failureTimer = window.setTimeout(() => {
        setFailure({
          message: "The connection response did not include one usable code.",
          isLink: Boolean(accountLinkCode) || flow === "link",
        });
      }, 0);
      return () => window.clearTimeout(failureTimer);
    }

    started.current = true;
    const destination = safeNextPath(requestedNext);
    if (accountLinkCode) {
      void completeOAuthLink(accountLinkCode)
        .then((user) => {
          setUser(user);
          setName(user.username);
          const label = isOAuthProvider(callbackProvider)
            ? providerLabels[callbackProvider]
            : "Account";
          showToast(`${label} is now connected.`);
          router.replace(destination);
        })
        .catch((reason: unknown) => {
          setFailure({
            message:
              reason instanceof Error
                ? reason.message
                : "This account connection is invalid or expired.",
            isLink: true,
          });
        });
      return;
    }

    void completeOAuth(loginCode)
      .then((user) => {
        setUser(user);
        setName(user.username);
        showToast(`Welcome, ${user.username}`);
        router.replace(destination);
      })
      .catch((reason: unknown) => {
        setFailure({
          message:
            reason instanceof Error ? reason.message : "This sign-in link is invalid or expired.",
          isLink: false,
        });
      });
  }, [code, error, flow, linkCode, next, provider, router, setName, setUser, showToast]);

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
        <Link
          href={failure.isLink ? "/profile" : "/profile?mode=login"}
          className="mt-6 inline-flex rounded-full bg-blossomdeep px-6 py-3 text-sm font-extrabold text-white shadow-glow"
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
