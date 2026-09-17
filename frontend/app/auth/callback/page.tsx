import OAuthCallbackClient from "./OAuthCallbackClient";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

export default async function OAuthCallbackPage({ searchParams }: { searchParams: SearchParams }) {
  const query = await searchParams;
  return (
    <main className="grid min-h-[calc(100vh-66px)] place-items-center bg-gradient-to-br from-[#ffe8f3] via-[#fff3f8] to-white px-5 py-10">
      <OAuthCallbackClient
        error={first(query.error)}
        flow={first(query.flow)}
        message={first(query.message)}
      />
    </main>
  );
}
