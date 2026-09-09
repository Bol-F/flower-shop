import PaymentReturnClient from "./PaymentReturnClient";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

export default async function PaymentReturnPage({ searchParams }: { searchParams: SearchParams }) {
  const query = await searchParams;
  const orderId = Number.parseInt(first(query.order), 10);
  return (
    <main className="grid min-h-[calc(100vh-66px)] place-items-center bg-gradient-to-br from-[#ffe8f3] via-[#fff3f8] to-white px-5 py-10">
      <PaymentReturnClient orderId={Number.isFinite(orderId) ? orderId : 0} paymentId={first(query.payment)} />
    </main>
  );
}
