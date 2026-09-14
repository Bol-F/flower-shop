"use client";

import { useEffect, useState } from "react";
import { fetchOAuthProviders, oauthStartUrl, type OAuthProvider } from "@/lib/api";

const providers: Array<{ id: OAuthProvider; label: string }> = [
  { id: "google", label: "Continue with Google" },
  { id: "github", label: "Continue with GitHub" },
  { id: "microsoft", label: "Continue with Microsoft" },
];

function ProviderIcon({ provider }: { provider: OAuthProvider }) {
  if (provider === "google") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="size-5">
        <path
          fill="#4285F4"
          d="M21.6 12.23c0-.71-.06-1.4-.18-2.07H12v3.92h5.38a4.6 4.6 0 0 1-2 3.02v2.54h3.24c1.9-1.75 2.98-4.32 2.98-7.41Z"
        />
        <path
          fill="#34A853"
          d="M12 22c2.7 0 4.97-.9 6.62-2.36l-3.24-2.54c-.9.6-2.05.96-3.38.96-2.6 0-4.81-1.76-5.6-4.13H3.05v2.62A10 10 0 0 0 12 22Z"
        />
        <path
          fill="#FBBC05"
          d="M6.4 13.93A6 6 0 0 1 6.09 12c0-.67.12-1.32.31-1.93V7.45H3.05A10 10 0 0 0 2 12c0 1.63.39 3.17 1.05 4.55l3.35-2.62Z"
        />
        <path
          fill="#EA4335"
          d="M12 5.94c1.47 0 2.79.5 3.83 1.5l2.87-2.88A9.62 9.62 0 0 0 12 2a10 10 0 0 0-8.95 5.45l3.35 2.62c.79-2.37 3-4.13 5.6-4.13Z"
        />
      </svg>
    );
  }
  if (provider === "github") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="size-5 fill-current">
        <path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.87c-2.78.6-3.37-1.18-3.37-1.18-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.35 1.09 2.92.83.09-.65.35-1.09.64-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02A9.56 9.56 0 0 1 12 6.82c.85 0 1.71.11 2.51.34 1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.86v2.76c0 .27.18.58.69.48A10 10 0 0 0 12 2Z" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="size-5">
      <path fill="#F25022" d="M2 2h9.5v9.5H2z" />
      <path fill="#7FBA00" d="M12.5 2H22v9.5h-9.5z" />
      <path fill="#00A4EF" d="M2 12.5h9.5V22H2z" />
      <path fill="#FFB900" d="M12.5 12.5H22V22h-9.5z" />
    </svg>
  );
}

export default function SocialLoginButtons({
  onNavigate = (provider: OAuthProvider) =>
    window.location.assign(oauthStartUrl(provider, "/profile")),
}: {
  onNavigate?: (provider: OAuthProvider) => void;
}) {
  const [enabled, setEnabled] = useState<Set<OAuthProvider> | null>(null);
  const [leavingFor, setLeavingFor] = useState<OAuthProvider | null>(null);

  useEffect(() => {
    let active = true;
    void fetchOAuthProviders()
      .then((items) => {
        if (active)
          setEnabled(new Set(items.filter((item) => item.enabled).map((item) => item.id)));
      })
      .catch(() => {
        if (active) setEnabled(new Set());
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="mt-6 grid gap-2" aria-label="Social sign in">
      {providers.map((provider) => {
        const capabilityLoaded = enabled !== null;
        const available = enabled?.has(provider.id) ?? false;
        const loading = leavingFor === provider.id;
        return (
          <button
            key={provider.id}
            type="button"
            disabled={!available || leavingFor !== null}
            onClick={() => {
              setLeavingFor(provider.id);
              onNavigate(provider.id);
            }}
            className="flex min-h-12 items-center justify-center gap-3 rounded-2xl border border-line bg-white px-4 py-3 text-sm font-extrabold text-ink transition hover:border-blossomdeep hover:bg-paper disabled:cursor-not-allowed disabled:opacity-50"
          >
            <ProviderIcon provider={provider.id} />
            <span>{loading ? "Opening provider…" : provider.label}</span>
            {!capabilityLoaded && (
              <span className="text-xs font-semibold text-stone">Checking…</span>
            )}
            {capabilityLoaded && !available && (
              <span className="text-xs font-semibold text-stone">Not configured</span>
            )}
          </button>
        );
      })}
      <div className="flex items-center gap-3 py-1" aria-hidden="true">
        <span className="h-px flex-1 bg-line" />
        <span className="text-xs font-bold uppercase tracking-widest text-stone">or use email</span>
        <span className="h-px flex-1 bg-line" />
      </div>
    </div>
  );
}
