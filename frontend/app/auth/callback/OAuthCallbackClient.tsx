"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { completeOAuth } from "@/lib/api";
import { useStore } from "@/lib/store";

function safeNextPath(value: string) {
  return value.startsWith("/") && !value.startsWith("//") ? value : "/profile";
}

export default function OAuthCallbackClient({
  code,
  error,
  message,
  next,
}: {
  code: string;
  error: string;
  message: string;
  next: string;
}) {
  const router = useRouter();
  const { setUser, setName, showToast } = useStore();
  const started = useRef(false);
  const [failure, setFailure] = useState(error ? message || "Sign-in was not completed." : "");

  useEffect(() => {
    if (started.current || error || !code) return;
    started.current = true;
    window.history.replaceState(null, "", "/auth/callback");
    void completeOAuth(code)
      .then((user) => {
        setUser(user);
        setName(user.username);
        showToast(`Welcome, ${user.username}`);
        router.replace(safeNextPath(next));
      })
      .catch((reason: unknown) => {
        setFailure(
          reason instanceof Error ? reason.message : "This sign-in link is invalid or expired.",
        );
      });
  }, [code, error, next, router, setName, setUser, showToast]);

  if (failure || (!code && !error)) {
    return (
      <section className="mx-auto max-w-lg rounded-[2rem] border border-line bg-white p-7 text-center shadow-lift">
        <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-berrysoft text-2xl">
          ×
        </div>
        <h1 className="mt-4 font-display text-3xl font-extrabold text-ink">Sign-in paused</h1>
        <p role="alert" className="mt-3 text-sm font-semibold leading-6 text-stone">
          {failure || "The sign-in response did not include a usable code."}
        </p>
        <Link
          href="/profile?mode=login"
          className="mt-6 inline-flex rounded-full bg-blossomdeep px-6 py-3 text-sm font-extrabold text-white shadow-glow"
        >
          Return to sign in
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
      <h1 className="mt-5 font-display text-3xl font-extrabold text-ink">Finishing sign-in</h1>
      <p className="mt-2 text-sm font-semibold text-stone">
        Securely exchanging your one-time code…
      </p>
    </section>
  );
}
