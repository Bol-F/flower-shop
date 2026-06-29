"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { fallbackCatalogProducts } from "@/lib/catalog";
import { formatPrice, toUzs } from "@/lib/currency";
import { copy, languages } from "@/lib/i18n";
import {
  API_BASE,
  ApiError,
  OfflineError,
  assignCourier,
  changePassword,
  fetchAdminDashboard,
  fetchCouriers,
  fetchAdminSupportMessages,
  fetchOrders,
  login as apiLogin,
  payTestOrder,
  repeatOrder,
  register as apiRegister,
  type ApiOrder,
  type ApiOrderStatus,
  type ApiOrderStatusStep,
  type ApiAdminDashboard,
  type ApiCourier,
  type ApiPaymentStatus,
  type AdminSupportMessage,
  updatePaymentStatus,
  updateOrderStatus,
  updateProfile,
} from "@/lib/api";
import { useStore } from "@/lib/store";
import type { Currency, Language } from "@/lib/types";
import ProductCard from "./ProductCard";
import {
  ArrowRightIcon,
  BoltIcon,
  CartIcon,
  HeartIcon,
  PinIcon,
  UserIcon,
} from "./icons";

const cities = ["Tashkent", "Samarkand", "Bukhara", "Namangan", "Andijan"];

const currencyOptions: Array<{
  id: Currency;
  label: string;
  symbol: string;
  note: string;
}> = [
  {
    id: "USD",
    label: "US Dollar",
    symbol: "$",
    note: "Default - prices as listed by florists",
  },
  {
    id: "UZS",
    label: "Uzbek so'm",
    symbol: "so'm",
    note: "Converted at the daily rate",
  },
];

type AuthMode = "register" | "login";

function firstApiMessage(error: unknown, fallback: string) {
  if (error instanceof OfflineError) return fallback;
  if (error instanceof ApiError) {
    const first = Object.values(error.details)[0];
    if (Array.isArray(first) && typeof first[0] === "string") return first[0];
    if (typeof first === "string") return first;
    return error.message;
  }
  return error instanceof Error ? error.message : fallback;
}

function formatAdminTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

const staffOrderStatuses: Array<{ id: ApiOrderStatus; label: string }> = [
  { id: "pending", label: "Pending" },
  { id: "confirmed", label: "Confirmed" },
  { id: "preparing", label: "Preparing" },
  { id: "courier_picked_up", label: "Courier picked up" },
  { id: "delivered", label: "Delivered" },
];

const paymentStatuses: Array<{ id: ApiPaymentStatus; label: string }> = [
  { id: "unpaid", label: "Unpaid" },
  { id: "pending", label: "Pending" },
  { id: "paid", label: "Paid" },
  { id: "failed", label: "Failed" },
  { id: "refunded", label: "Refunded" },
];

function formatDeliveryDate(value: string | null) {
  if (!value) return "Not selected";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function deliveryMapUrl(order: ApiOrder) {
  if (!order.delivery_lat || !order.delivery_lng) return null;
  return `https://www.openstreetmap.org/?mlat=${order.delivery_lat}&mlon=${order.delivery_lng}#map=16/${order.delivery_lat}/${order.delivery_lng}`;
}

function OrderStatusTimeline({ steps }: { steps: ApiOrderStatusStep[] }) {
  if (steps.length === 0) return null;

  return (
    <ol className="mt-4 grid gap-2 sm:grid-cols-5">
      {steps.map((step) => (
        <li
          key={step.id}
          aria-current={step.active ? "step" : undefined}
          className={`rounded-2xl border px-3 py-2 text-xs font-extrabold ${
            step.active
              ? "border-blossomdeep bg-blossomdeep text-white shadow-glow"
              : step.completed
                ? "border-[#bfe6cc] bg-mint text-leaf"
                : "border-line bg-white text-stone"
          }`}
        >
          {step.label}
        </li>
      ))}
    </ol>
  );
}

const badgeBase = "rounded-full px-3 py-1 text-xs font-extrabold";

function orderStatusBadgeClass(status: ApiOrderStatus) {
  if (status === "delivered") return "bg-mint text-leaf";
  if (status === "cancelled") return "bg-berrysoft text-berry";
  if (status === "courier_picked_up") return "bg-lilac text-iris";
  if (status === "preparing") return "bg-[#fff3d8] text-[#9a6410]";
  if (status === "confirmed") return "bg-skywash text-ink";
  return "bg-blush text-blossomdeep";
}

function paymentStatusBadgeClass(status: ApiPaymentStatus) {
  if (status === "paid") return "bg-mint text-leaf";
  if (status === "failed") return "bg-berrysoft text-berry";
  if (status === "refunded") return "bg-lilac text-iris";
  if (status === "pending") return "bg-[#fff3d8] text-[#9a6410]";
  return "bg-paper text-stone";
}

function LoadingRows({ label = "Loading" }: { label?: string }) {
  return (
    <div className="grid gap-3 px-5 py-5">
      {[0, 1, 2].map((item) => (
        <div key={item} className="animate-pulse rounded-3xl border border-line p-4">
          <div className="h-4 w-36 rounded-full bg-line" />
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            <div className="h-3 rounded-full bg-line" />
            <div className="h-3 rounded-full bg-line" />
            <div className="h-3 rounded-full bg-line" />
          </div>
        </div>
      ))}
      <p className="sr-only">{label}</p>
    </div>
  );
}

function EmptyPanel({
  title,
  text,
  action,
}: {
  title: string;
  text: string;
  action?: ReactNode;
}) {
  return (
    <div className="px-5 py-8 text-center">
      <div className="mx-auto grid size-12 place-items-center rounded-2xl bg-blush text-lg font-extrabold text-blossomdeep">
        0
      </div>
      <p className="mt-3 font-display text-xl font-bold text-ink">{title}</p>
      <p className="mx-auto mt-1 max-w-md text-sm font-semibold text-stone">
        {text}
      </p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

function staffInitials(name: string, email: string) {
  const source = (name || email || "Admin").trim();
  return source.slice(0, 2).toUpperCase();
}

function buildAdminConversations(messages: AdminSupportMessage[]) {
  const grouped = new Map<string, AdminSupportMessage[]>();

  for (const message of messages) {
    const key = message.user_email || `message-${message.id}`;
    grouped.set(key, [...(grouped.get(key) ?? []), message]);
  }

  return [...grouped.entries()]
    .map(([key, group]) => {
      const ordered = [...group].sort(
        (a, b) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      );
      const lastMessage = ordered[ordered.length - 1];
      return {
        key,
        name: lastMessage.user_username || lastMessage.user_email || "Customer",
        email: lastMessage.user_email,
        messages: ordered,
        lastMessage,
        unread: ordered.filter(
          (message) => !message.is_from_admin && !message.is_read,
        ).length,
        waiting: !lastMessage.is_from_admin,
      };
    })
    .sort(
      (a, b) =>
        new Date(b.lastMessage.created_at).getTime() -
        new Date(a.lastMessage.created_at).getTime(),
    );
}

function AdminWorkspace() {
  const {
    user,
    name,
    setUser,
    setName,
    signOut,
    language,
    setLanguage,
    showToast,
  } = useStore();
  const [messages, setMessages] = useState<AdminSupportMessage[]>([]);
  const [supportLoading, setSupportLoading] = useState(true);
  const [supportError, setSupportError] = useState("");
  const [orders, setOrders] = useState<ApiOrder[]>([]);
  const [couriers, setCouriers] = useState<ApiCourier[]>([]);
  const [dashboard, setDashboard] = useState<ApiAdminDashboard | null>(null);
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [ordersError, setOrdersError] = useState("");
  const [statusFilter, setStatusFilter] = useState<ApiOrderStatus | "all">("all");
  const [paymentFilter, setPaymentFilter] =
    useState<"all" | "cash" | "card" | "online">("all");
  const [paymentStatusFilter, setPaymentStatusFilter] =
    useState<ApiPaymentStatus | "all">("all");
  const [deliveryZoneFilter, setDeliveryZoneFilter] = useState("all");
  const [deliveryDateFilter, setDeliveryDateFilter] = useState("");
  const [cityFilter, setCityFilter] = useState("all");
  const [courierFilter, setCourierFilter] = useState("all");
  const [updatingOrderId, setUpdatingOrderId] = useState<number | null>(null);
  const [updatingPaymentId, setUpdatingPaymentId] = useState<number | null>(null);
  const [assigningCourierOrderId, setAssigningCourierOrderId] = useState<number | null>(null);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirm, setNewPasswordConfirm] = useState("");

  const conversations = useMemo(
    () => buildAdminConversations(messages),
    [messages],
  );
  const filteredOrders = useMemo(
    () =>
      orders.filter((order) => {
        const matchesStatus = statusFilter === "all" || order.status === statusFilter;
        const matchesPayment =
          paymentFilter === "all" || order.payment_method === paymentFilter;
        const matchesPaymentStatus =
          paymentStatusFilter === "all" ||
          order.payment_status === paymentStatusFilter;
        const matchesZone =
          deliveryZoneFilter === "all" ||
          String(order.delivery_zone?.id ?? "none") === deliveryZoneFilter;
        const matchesDeliveryDate =
          !deliveryDateFilter || order.delivery_date === deliveryDateFilter;
        const matchesCity =
          cityFilter === "all" || (order.city_slug ?? "none") === cityFilter;
        const matchesCourier =
          courierFilter === "all" ||
          String(order.assigned_courier_id ?? "none") === courierFilter;
        return (
          matchesStatus &&
          matchesPayment &&
          matchesPaymentStatus &&
          matchesZone &&
          matchesDeliveryDate &&
          matchesCity &&
          matchesCourier
        );
      }),
    [
      cityFilter,
      courierFilter,
      deliveryDateFilter,
      deliveryZoneFilter,
      orders,
      paymentFilter,
      paymentStatusFilter,
      statusFilter,
    ],
  );
  const deliveryZoneOptions = useMemo(
    () =>
      Array.from(
        new Map(
          orders
            .filter((order) => order.delivery_zone)
            .map((order) => [
              String(order.delivery_zone?.id),
              order.delivery_zone?.name ?? "",
            ]),
        ).entries(),
      ),
    [orders],
  );
  const cityOptions = useMemo(
    () =>
      Array.from(
        new Map(
          orders
            .filter((order) => order.city_slug)
            .map((order) => [order.city_slug ?? "", order.city_name ?? ""]),
        ).entries(),
      ),
    [orders],
  );
  const lastCustomerMessage = messages.find((message) => !message.is_from_admin);
  const displayName = name || user?.username || "Admin";

  useEffect(() => {
    if (!user?.is_staff) return;
    let active = true;

    async function loadSupport(showSpinner = false) {
      try {
        if (showSpinner) setSupportLoading(true);
        const data = await fetchAdminSupportMessages();
        if (active) {
          setMessages(data);
          setSupportError("");
        }
      } catch (err) {
        if (active) {
          setSupportError(firstApiMessage(err, "Could not load support queue."));
        }
      } finally {
        if (active) setSupportLoading(false);
      }
    }

    const firstLoad = window.setTimeout(() => {
      void loadSupport(true);
    }, 0);
    const timer = window.setInterval(() => {
      void loadSupport(false);
    }, 10000);

    return () => {
      active = false;
      window.clearTimeout(firstLoad);
      window.clearInterval(timer);
    };
  }, [user?.is_staff]);

  useEffect(() => {
    if (!user?.is_staff) return;
    let active = true;

    async function loadOrders(showSpinner = false) {
      try {
        if (showSpinner) setOrdersLoading(true);
        const [data, dashboardData, courierData] = await Promise.all([
          fetchOrders(),
          fetchAdminDashboard(),
          fetchCouriers(),
        ]);
        if (active) {
          setOrders(data);
          setDashboard(dashboardData);
          setCouriers(courierData);
          setOrdersError("");
        }
      } catch (err) {
        if (active) setOrdersError(firstApiMessage(err, "Could not load orders."));
      } finally {
        if (active) setOrdersLoading(false);
      }
    }

    void loadOrders(true);
    const timer = window.setInterval(() => {
      void loadOrders(false);
    }, 15000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [user?.is_staff]);

  if (!user?.is_staff) return null;

  async function onOrderStatusChange(orderId: number, nextStatus: ApiOrderStatus) {
    setOrdersError("");
    try {
      setUpdatingOrderId(orderId);
      const updated = await updateOrderStatus(orderId, nextStatus);
      setOrders((current) =>
        current.map((order) => (order.id === updated.id ? updated : order)),
      );
      showToast(`Order #${updated.id} marked ${updated.status_display}`);
    } catch (err) {
      setOrdersError(firstApiMessage(err, "Could not update order status."));
    } finally {
      setUpdatingOrderId(null);
    }
  }

  async function onPaymentStatusChange(
    orderId: number,
    nextStatus: ApiPaymentStatus,
  ) {
    setOrdersError("");
    try {
      setUpdatingPaymentId(orderId);
      const updated = await updatePaymentStatus(orderId, nextStatus);
      setOrders((current) =>
        current.map((order) => (order.id === updated.id ? updated : order)),
      );
      showToast(`Order #${updated.id} payment marked ${updated.payment_status_display}`);
    } catch (err) {
      setOrdersError(firstApiMessage(err, "Could not update payment status."));
    } finally {
      setUpdatingPaymentId(null);
    }
  }

  async function onCourierAssign(orderId: number, courierId: number | null) {
    setOrdersError("");
    try {
      setAssigningCourierOrderId(orderId);
      const updated = await assignCourier(orderId, courierId);
      setOrders((current) =>
        current.map((order) => (order.id === updated.id ? updated : order)),
      );
      showToast(
        courierId
          ? `Courier assigned to order #${updated.id}`
          : `Courier removed from order #${updated.id}`,
      );
    } catch (err) {
      setOrdersError(firstApiMessage(err, "Could not assign courier."));
    } finally {
      setAssigningCourierOrderId(null);
    }
  }

  async function onAdminProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) return;
    setProfileError("");

    const form = new FormData(event.currentTarget);
    const nextLanguage = String(form.get("language") || language) as Language;

    try {
      setProfileSaving(true);
      const updated = await updateProfile({
        username: String(form.get("username") || user.username),
        phone: String(form.get("phone") || ""),
        language: nextLanguage,
      });
      setUser(updated);
      setName(updated.username);
      setLanguage(updated.language);
      showToast("Admin profile updated");
    } catch (err) {
      setProfileError(firstApiMessage(err, "Could not update admin profile."));
    } finally {
      setProfileSaving(false);
    }
  }

  async function onAdminPasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError("");

    if (newPassword !== newPasswordConfirm) {
      setPasswordError("New passwords do not match.");
      return;
    }

    try {
      setPasswordSaving(true);
      await changePassword({
        old_password: oldPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      });
      setOldPassword("");
      setNewPassword("");
      setNewPasswordConfirm("");
      showToast("Password changed");
    } catch (err) {
      setPasswordError(firstApiMessage(err, "Could not change password."));
    } finally {
      setPasswordSaving(false);
    }
  }

  const statCards = [
    {
      label: "Today",
      value: dashboard?.today_orders ?? orders.length,
      detail: ordersLoading ? "Syncing orders" : "Orders created today",
    },
    {
      label: "Pending",
      value: dashboard?.pending_orders ?? 0,
      detail: "Need confirmation",
    },
    {
      label: "Preparing",
      value: dashboard?.preparing_orders ?? 0,
      detail: "Being arranged",
    },
    {
      label: "Revenue today",
      value: formatPrice(
        Number.parseFloat(dashboard?.total_revenue_today ?? "0") || 0,
        user.currency,
      ),
      detail: "Non-cancelled orders",
    },
  ];
  const deliveryQueue = dashboard?.delivery_queue ?? [];

  return (
    <main className="min-h-[calc(100vh-66px)] bg-[#f6f7fb] px-4 py-8">
      <section className="mx-auto max-w-7xl">
        <div className="flex flex-wrap items-center gap-4 rounded-[1.75rem] border border-line bg-white px-5 py-5 shadow-soft">
          <span className="grid size-14 place-items-center rounded-2xl bg-ink text-base font-extrabold text-white shadow-soft">
            {staffInitials(displayName, user.email)}
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-3xl font-extrabold text-ink sm:text-4xl">
                Admin workspace
              </h1>
              <span className="rounded-full bg-[#e8f6ee] px-3 py-1 text-xs font-extrabold uppercase tracking-wider text-[#1f7a4d]">
                Staff
              </span>
            </div>
            <p className="mt-1 truncate text-sm font-semibold text-stone">
              {displayName} / {user.email}
            </p>
          </div>
          <div className="ml-auto flex flex-wrap gap-2">
            <Link
              href="/admin"
              className="inline-flex items-center gap-2 rounded-full bg-blossomdeep px-5 py-2.5 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry"
            >
              Support inbox
              <ArrowRightIcon className="size-4" />
            </Link>
            <button
              type="button"
              onClick={signOut}
              className="rounded-full border border-line px-5 py-2.5 text-sm font-bold text-stone transition hover:border-blossomdeep hover:text-blossomdeep"
            >
              Sign out
            </button>
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {statCards.map((card) => (
            <section
              key={card.label}
              className="rounded-[1.35rem] border border-line bg-white p-5 shadow-soft"
            >
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-stone">
                {card.label}
              </p>
              <p className="mt-3 font-display text-4xl font-extrabold text-ink">
                {card.value}
              </p>
              <p className="mt-1 text-sm font-semibold text-stone">
                {card.detail}
              </p>
            </section>
          ))}
        </div>

        <section className="mt-5 rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-2xl font-extrabold text-ink">
                Delivery queue
              </h2>
              <p className="mt-0.5 text-sm font-semibold text-stone">
                Active orders that staff and couriers should watch first
              </p>
            </div>
            <span className="rounded-full bg-blush px-3 py-1 text-xs font-extrabold text-blossomdeep">
              {deliveryQueue.length} active
            </span>
          </div>
          {ordersLoading && !dashboard ? (
            <LoadingRows label="Loading delivery queue" />
          ) : deliveryQueue.length === 0 ? (
            <EmptyPanel
              title="No active deliveries"
              text="Confirmed, preparing, and courier-picked-up orders will appear here."
            />
          ) : (
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {deliveryQueue.slice(0, 4).map((order) => (
                <article
                  key={order.id}
                  className="rounded-3xl border border-line bg-paper p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-display text-lg font-bold text-ink">
                        Order #{order.id}
                      </p>
                      <p className="mt-1 text-xs font-semibold text-stone">
                        {order.recipient_name || "Recipient"} /{" "}
                        {formatDeliveryDate(order.delivery_date)}
                      </p>
                    </div>
                    <span className={`${badgeBase} ${orderStatusBadgeClass(order.status)}`}>
                      {order.status_display}
                    </span>
                  </div>
                  <p className="mt-3 text-sm font-semibold text-ink">
                    {order.delivery_time_slot_display || order.delivery_time_slot}
                  </p>
                  <p className="mt-1 line-clamp-2 text-sm text-stone">
                    {order.delivery_address || order.shipping_address}
                  </p>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="mt-5 rounded-[1.75rem] border border-line bg-white shadow-soft">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4">
            <div>
              <h2 className="font-display text-2xl font-extrabold text-ink">
                Delivery orders
              </h2>
              <p className="mt-0.5 text-sm font-semibold text-stone">
                {ordersError || "Filter and update active flower deliveries"}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <select
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(event.target.value as ApiOrderStatus | "all")
                }
                className="rounded-full border border-line bg-paper px-4 py-2 text-sm font-bold outline-none transition focus:border-blossomdeep"
              >
                <option value="all">All statuses</option>
                {staffOrderStatuses.map((status) => (
                  <option key={status.id} value={status.id}>
                    {status.label}
                  </option>
                ))}
                <option value="cancelled">Cancelled</option>
              </select>
              <select
                value={paymentFilter}
                onChange={(event) =>
                  setPaymentFilter(
                    event.target.value as "all" | "cash" | "card" | "online",
                  )
                }
                className="rounded-full border border-line bg-paper px-4 py-2 text-sm font-bold outline-none transition focus:border-blossomdeep"
              >
                <option value="all">All payments</option>
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="online">Online</option>
              </select>
              <select
                value={paymentStatusFilter}
                onChange={(event) =>
                  setPaymentStatusFilter(event.target.value as ApiPaymentStatus | "all")
                }
                className="rounded-full border border-line bg-paper px-4 py-2 text-sm font-bold outline-none transition focus:border-blossomdeep"
              >
                <option value="all">All payment statuses</option>
                {paymentStatuses.map((paymentStatus) => (
                  <option key={paymentStatus.id} value={paymentStatus.id}>
                    {paymentStatus.label}
                  </option>
                ))}
              </select>
              <select
                value={deliveryZoneFilter}
                onChange={(event) => setDeliveryZoneFilter(event.target.value)}
                className="rounded-full border border-line bg-paper px-4 py-2 text-sm font-bold outline-none transition focus:border-blossomdeep"
              >
                <option value="all">All zones</option>
                <option value="none">No zone</option>
                {deliveryZoneOptions.map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                  ))}
              </select>
              <select
                value={cityFilter}
                onChange={(event) => setCityFilter(event.target.value)}
                className="rounded-full border border-line bg-paper px-4 py-2 text-sm font-bold outline-none transition focus:border-blossomdeep"
              >
                <option value="all">All cities</option>
                <option value="none">No city</option>
                {cityOptions.map(([slug, name]) => (
                  <option key={slug} value={slug}>
                    {name}
                  </option>
                ))}
              </select>
              <select
                value={courierFilter}
                onChange={(event) => setCourierFilter(event.target.value)}
                className="rounded-full border border-line bg-paper px-4 py-2 text-sm font-bold outline-none transition focus:border-blossomdeep"
              >
                <option value="all">All couriers</option>
                <option value="none">Unassigned courier</option>
                {couriers.map((courier) => (
                  <option key={courier.id} value={courier.id}>
                    {courier.user_username || courier.user_email}
                  </option>
                ))}
              </select>
              <input
                type="date"
                value={deliveryDateFilter}
                onChange={(event) => setDeliveryDateFilter(event.target.value)}
                className="rounded-full border border-line bg-paper px-4 py-2 text-sm font-bold outline-none transition focus:border-blossomdeep"
                aria-label="Filter by delivery date"
              />
              {deliveryDateFilter && (
                <button
                  type="button"
                  onClick={() => setDeliveryDateFilter("")}
                  className="rounded-full border border-line px-4 py-2 text-sm font-extrabold text-stone transition hover:border-blossomdeep hover:text-blossomdeep"
                >
                  Clear date
                </button>
              )}
              <a
                href={`${API_BASE}/admin/orders/order/delivery-map/`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full bg-blush px-4 py-2 text-sm font-extrabold text-blossomdeep transition hover:bg-blushdeep"
              >
                Delivery map
                <ArrowRightIcon className="size-4" />
              </a>
            </div>
          </div>

          <div className="divide-y divide-line">
            {ordersLoading && orders.length === 0 && (
              <LoadingRows label="Loading delivery orders" />
            )}
            {!ordersLoading && filteredOrders.length === 0 && (
              <EmptyPanel
                title="No orders match"
                text="Clear filters or run seed_demo to populate realistic delivery orders."
                action={
                  <button
                    type="button"
                    onClick={() => {
                      setStatusFilter("all");
                      setPaymentFilter("all");
                      setPaymentStatusFilter("all");
                      setDeliveryZoneFilter("all");
                      setDeliveryDateFilter("");
                      setCityFilter("all");
                      setCourierFilter("all");
                    }}
                    className="rounded-full bg-blossomdeep px-5 py-2.5 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry"
                  >
                    Clear filters
                  </button>
                }
              />
            )}
            {filteredOrders.slice(0, 8).map((order) => {
              const subtotal = Number.parseFloat(order.subtotal_price) || 0;
              const deliveryFee = Number.parseFloat(order.delivery_fee) || 0;
              const total = Number.parseFloat(order.total_price) || 0;
              const mapUrl = deliveryMapUrl(order);

              return (
                <article key={order.id} className="px-5 py-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-display text-xl font-bold text-ink">
                        Order #{order.id}
                      </p>
                      <p className="mt-1 text-xs font-semibold text-stone">
                        {formatAdminTime(order.created_at)}
                      </p>
                      <p className="mt-1 text-xs font-semibold text-stone">
                        {order.user_username || "Customer"} / {order.user_email}
                      </p>
                    </div>
                    <div className="flex flex-wrap justify-end gap-1.5">
                      <span className={`${badgeBase} ${orderStatusBadgeClass(order.status)}`}>
                        {order.status_display}
                      </span>
                      <span className={`${badgeBase} bg-white text-stone ring-1 ring-line`}>
                        {order.payment_method_display}
                      </span>
                      <span className={`${badgeBase} ${paymentStatusBadgeClass(order.payment_status)}`}>
                        {order.payment_status_display}
                      </span>
                      <span className="rounded-full bg-ink px-3 py-1 text-xs font-extrabold text-white">
                        {formatPrice(total, user.currency)}
                      </span>
                    </div>
                  </div>

                  <OrderStatusTimeline steps={order.status_timeline} />

                  <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                    <div>
                      <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                        Recipient
                      </p>
                      <p className="mt-1 font-bold text-ink">
                        {order.recipient_name || "Not provided"}
                      </p>
                      <p className="text-stone">
                        {order.recipient_phone || order.phone}
                      </p>
                      {order.call_recipient_before_delivery && (
                        <p className="mt-1 text-xs font-bold text-leaf">
                          Call before delivery
                        </p>
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                        Delivery
                      </p>
                      <p className="mt-1 font-bold text-ink">
                        {formatDeliveryDate(order.delivery_date)}
                      </p>
                      <p className="text-stone">
                        {order.delivery_time_slot_display || order.delivery_time_slot}
                      </p>
                      <p className="mt-1 text-stone">
                        {order.delivery_zone?.name || "No zone selected"}
                      </p>
                      <p className="mt-1 text-stone">
                        {order.city_name || "No city"} / {order.vendor_name || "No vendor"}
                      </p>
                      <p className="mt-1 text-stone">
                        Courier {order.assigned_courier_name || "unassigned"}
                      </p>
                      {order.delivery_requires_confirmation && (
                        <p className="mt-1 text-xs font-bold text-[#9a6410]">
                          Manual delivery confirmation
                        </p>
                      )}
                    </div>
                    <div>
                      <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                        Payment
                      </p>
                      <p className="mt-1 text-stone">
                        {order.payment_method_display} / {order.payment_status_display}
                      </p>
                      <p className="text-stone">
                        Provider {order.payment_provider || "manual"}
                      </p>
                      {order.payment_reference && (
                        <p className="text-stone">
                          Ref {order.payment_reference}
                        </p>
                      )}
                      {order.paid_at && (
                        <p className="text-leaf">
                          Paid {formatAdminTime(order.paid_at)}
                        </p>
                      )}
                      <p className="mt-2 text-xs font-extrabold uppercase tracking-wider text-stone">
                        Totals
                      </p>
                      <p className="text-stone">
                        Items {formatPrice(subtotal, user.currency)}
                      </p>
                      <p className="text-stone">
                        Delivery{" "}
                        {deliveryFee === 0
                          ? "Free"
                          : formatPrice(deliveryFee, user.currency)}
                      </p>
                    </div>
                  </div>

                  <p className="mt-3 text-sm text-stone">
                    {order.delivery_address || order.shipping_address}
                    {mapUrl && (
                      <a
                        href={mapUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="ml-2 font-extrabold text-blossomdeep hover:text-raspberry"
                      >
                        Open map
                      </a>
                    )}
                  </p>
                  {order.gift_note && (
                    <p className="mt-2 rounded-2xl bg-paper px-4 py-3 text-sm font-semibold text-ink">
                      {order.gift_note}
                    </p>
                  )}

                  <div className="mt-4 flex flex-wrap gap-2">
                    <select
                      value={order.assigned_courier_id ?? "none"}
                      disabled={assigningCourierOrderId === order.id}
                      onChange={(event) => {
                        const next = event.target.value;
                        void onCourierAssign(
                          order.id,
                          next === "none" ? null : Number(next),
                        );
                      }}
                      className="rounded-full border border-line px-3 py-1.5 text-xs font-extrabold text-stone outline-none transition hover:border-blossomdeep hover:text-blossomdeep disabled:cursor-wait disabled:opacity-45"
                    >
                      <option value="none">Assign courier</option>
                      {couriers.map((courier) => (
                        <option key={courier.id} value={courier.id}>
                          {courier.user_username || courier.user_email}
                        </option>
                      ))}
                    </select>
                    {staffOrderStatuses
                      .filter((status) => status.id !== "pending")
                      .map((status) => (
                        <button
                          key={status.id}
                          type="button"
                          disabled={
                            updatingOrderId === order.id || order.status === status.id
                          }
                          onClick={() => void onOrderStatusChange(order.id, status.id)}
                          className="rounded-full border border-line px-3 py-1.5 text-xs font-extrabold text-stone transition hover:border-blossomdeep hover:text-blossomdeep disabled:cursor-not-allowed disabled:opacity-45"
                        >
                          {updatingOrderId === order.id ? "Updating..." : status.label}
                        </button>
                      ))}
                    <button
                      type="button"
                      disabled={
                        updatingPaymentId === order.id ||
                        order.payment_status === "paid"
                      }
                      onClick={() => void onPaymentStatusChange(order.id, "paid")}
                      className="rounded-full border border-line px-3 py-1.5 text-xs font-extrabold text-stone transition hover:border-leaf hover:text-leaf disabled:cursor-not-allowed disabled:opacity-45"
                    >
                      {updatingPaymentId === order.id ? "Updating..." : "Payment paid"}
                    </button>
                    <button
                      type="button"
                      disabled={
                        updatingPaymentId === order.id ||
                        order.payment_status === "failed"
                      }
                      onClick={() => void onPaymentStatusChange(order.id, "failed")}
                      className="rounded-full border border-line px-3 py-1.5 text-xs font-extrabold text-stone transition hover:border-berry hover:text-berry disabled:cursor-not-allowed disabled:opacity-45"
                    >
                      {updatingPaymentId === order.id ? "Updating..." : "Payment failed"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <div className="mt-5 grid gap-5 lg:grid-cols-3">
          <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
            <h2 className="font-display text-2xl font-extrabold text-ink">
              Low stock
            </h2>
            <div className="mt-4 grid gap-2">
              {(dashboard?.low_stock_products ?? []).slice(0, 5).map((product) => (
                <Link
                  key={product.id}
                  href={`/product/${product.slug}`}
                  className="flex items-center justify-between rounded-2xl border border-line px-4 py-3 text-sm transition hover:border-blossomdeep"
                >
                  <span className="min-w-0 truncate font-bold">{product.name}</span>
                  <span className="shrink-0 text-xs font-extrabold text-[#9a6410]">
                    {product.stock} left
                  </span>
                </Link>
              ))}
              {(dashboard?.low_stock_products ?? []).length === 0 && (
                <p className="rounded-2xl bg-paper px-4 py-3 text-sm font-semibold text-stone">
                  No low-stock products.
                </p>
              )}
            </div>
          </section>

          <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
            <h2 className="font-display text-2xl font-extrabold text-ink">
              Out of stock
            </h2>
            <div className="mt-4 grid gap-2">
              {(dashboard?.out_of_stock_products ?? []).slice(0, 5).map((product) => (
                <Link
                  key={product.id}
                  href={`/product/${product.slug}`}
                  className="flex items-center justify-between rounded-2xl border border-line px-4 py-3 text-sm transition hover:border-blossomdeep"
                >
                  <span className="min-w-0 truncate font-bold">{product.name}</span>
                  <span className="shrink-0 text-xs font-extrabold text-berry">
                    Restock
                  </span>
                </Link>
              ))}
              {(dashboard?.out_of_stock_products ?? []).length === 0 && (
                <p className="rounded-2xl bg-paper px-4 py-3 text-sm font-semibold text-stone">
                  No out-of-stock products.
                </p>
              )}
            </div>
          </section>

          <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
            <h2 className="font-display text-2xl font-extrabold text-ink">
              Best sellers
            </h2>
            <div className="mt-4 grid gap-2">
              {(dashboard?.best_selling_products ?? []).slice(0, 5).map((product) => (
                <div
                  key={product.product_name}
                  className="flex items-center justify-between rounded-2xl border border-line px-4 py-3 text-sm"
                >
                  <span className="min-w-0 truncate font-bold">
                    {product.product_name}
                  </span>
                  <span className="shrink-0 text-xs font-extrabold text-leaf">
                    {product.quantity_sold} sold
                  </span>
                </div>
              ))}
              {(dashboard?.best_selling_products ?? []).length === 0 && (
                <p className="rounded-2xl bg-paper px-4 py-3 text-sm font-semibold text-stone">
                  No sales data yet.
                </p>
              )}
            </div>
          </section>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-4">
          <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
            <h2 className="font-display text-xl font-extrabold text-ink">
              Revenue by day
            </h2>
            <div className="mt-4 grid gap-2">
              {(dashboard?.revenue_by_day ?? []).slice(0, 5).map((item) => (
                <div key={item.date ?? "unknown"} className="flex justify-between text-sm">
                  <span className="font-semibold text-stone">{item.date ?? "Unknown"}</span>
                  <span className="font-extrabold text-ink">
                    {formatPrice(Number.parseFloat(item.revenue) || 0, user.currency)}
                  </span>
                </div>
              ))}
              {(dashboard?.revenue_by_day ?? []).length === 0 && (
                <p className="text-sm font-semibold text-stone">No revenue yet.</p>
              )}
            </div>
          </section>

          <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
            <h2 className="font-display text-xl font-extrabold text-ink">
              Payment status
            </h2>
            <div className="mt-4 grid gap-2">
              {(dashboard?.payment_status_summary ?? []).map((item) => (
                <div key={item.payment_status} className="flex justify-between text-sm">
                  <span className="font-semibold capitalize text-stone">
                    {item.payment_status}
                  </span>
                  <span className="font-extrabold text-ink">{item.count}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
            <h2 className="font-display text-xl font-extrabold text-ink">
              Cities
            </h2>
            <div className="mt-4 grid gap-2">
              {(dashboard?.city_order_summary ?? []).map((item) => (
                <div key={item.city} className="flex justify-between text-sm">
                  <span className="font-semibold text-stone">{item.city}</span>
                  <span className="font-extrabold text-ink">{item.count}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
            <h2 className="font-display text-xl font-extrabold text-ink">
              Top customers
            </h2>
            <div className="mt-4 grid gap-2">
              {(dashboard?.top_customers ?? []).slice(0, 5).map((item) => (
                <div key={item.email} className="min-w-0 text-sm">
                  <p className="truncate font-extrabold text-ink">
                    {item.username || item.email}
                  </p>
                  <p className="text-stone">
                    {item.orders} orders / {formatPrice(Number.parseFloat(item.revenue) || 0, user.currency)}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="mt-5 grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
          <section className="rounded-[1.75rem] border border-line bg-white shadow-soft">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4">
              <div>
                <h2 className="font-display text-2xl font-extrabold text-ink">
                  Support queue
                </h2>
                <p className="mt-0.5 text-sm font-semibold text-stone">
                  {supportError || "Newest customer conversations"}
                </p>
              </div>
              <Link
                href="/admin"
                className="inline-flex items-center gap-2 rounded-full bg-blush px-4 py-2 text-sm font-extrabold text-blossomdeep transition hover:bg-blushdeep"
              >
                Open chats
                <ArrowRightIcon className="size-4" />
              </Link>
            </div>

            <div className="divide-y divide-line">
              {supportLoading && conversations.length === 0 && (
                <p className="px-5 py-8 text-sm font-bold text-stone">
                  Loading support queue...
                </p>
              )}
              {!supportLoading && conversations.length === 0 && (
                <p className="px-5 py-8 text-sm font-bold text-stone">
                  No support conversations yet.
                </p>
              )}
              {conversations.slice(0, 5).map((conversation) => (
                <Link
                  key={conversation.key}
                  href="/admin"
                  className="flex items-center gap-3 px-5 py-4 transition hover:bg-[#fff8fb]"
                >
                  <span className="grid size-11 shrink-0 place-items-center rounded-full bg-blush text-sm font-extrabold text-blossomdeep">
                    {staffInitials(conversation.name, conversation.email)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2">
                      <span className="truncate text-sm font-extrabold text-ink">
                        {conversation.name}
                      </span>
                      {conversation.waiting && (
                        <span className="rounded-full bg-[#fff3d8] px-2 py-0.5 text-[11px] font-extrabold text-[#9a6410]">
                          Waiting
                        </span>
                      )}
                    </span>
                    <span className="mt-0.5 block truncate text-sm text-stone">
                      {conversation.lastMessage.is_from_admin ? "You: " : ""}
                      {conversation.lastMessage.body}
                    </span>
                  </span>
                  <span className="shrink-0 text-right">
                    <span className="block text-xs font-bold text-stone">
                      {formatAdminTime(conversation.lastMessage.created_at)}
                    </span>
                    {conversation.unread > 0 && (
                      <span className="mt-1 inline-grid min-w-5 place-items-center rounded-full bg-blossomdeep px-1.5 text-[11px] font-extrabold text-white">
                        {conversation.unread}
                      </span>
                    )}
                  </span>
                </Link>
              ))}
            </div>
          </section>

          <aside className="grid gap-5">
            <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
              <h2 className="font-display text-2xl font-extrabold text-ink">
                Tools
              </h2>
              <div className="mt-4 grid gap-3">
                <Link
                  href="/admin"
                  className="flex items-center justify-between rounded-2xl border border-line px-4 py-3 text-sm font-extrabold text-ink transition hover:border-blossomdeep hover:text-blossomdeep"
                >
                  <span className="flex items-center gap-2">
                    <BoltIcon className="size-4" />
                    Support inbox
                  </span>
                  <ArrowRightIcon className="size-4" />
                </Link>
                <a
                  href={`${API_BASE}/admin/`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between rounded-2xl border border-line px-4 py-3 text-sm font-extrabold text-ink transition hover:border-blossomdeep hover:text-blossomdeep"
                >
                  <span className="flex items-center gap-2">
                    <UserIcon className="size-4" />
                    Django admin
                  </span>
                  <ArrowRightIcon className="size-4" />
                </a>
                <Link
                  href="/#catalog"
                  className="flex items-center justify-between rounded-2xl border border-line px-4 py-3 text-sm font-extrabold text-ink transition hover:border-blossomdeep hover:text-blossomdeep"
                >
                  <span className="flex items-center gap-2">
                    <CartIcon className="size-4" />
                    Storefront catalog
                  </span>
                  <ArrowRightIcon className="size-4" />
                </Link>
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-line bg-ink p-5 text-white shadow-soft">
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-white/60">
                Last customer activity
              </p>
              <p className="mt-3 text-sm leading-relaxed text-white/85">
                {lastCustomerMessage
                  ? `${lastCustomerMessage.user_username || lastCustomerMessage.user_email}: ${lastCustomerMessage.body}`
                  : "No customer messages have arrived yet."}
              </p>
            </section>
          </aside>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
            <h2 className="font-display text-2xl font-extrabold text-ink">
              Team account
            </h2>
            <form
              onSubmit={onAdminProfileSubmit}
              className="mt-5 grid gap-4 sm:grid-cols-2"
            >
              <label className="block">
                <span className="text-sm font-bold uppercase tracking-wider text-stone">
                  Display name
                </span>
                <input
                  name="username"
                  defaultValue={user.username}
                  className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
                />
              </label>

              <label className="block">
                <span className="text-sm font-bold uppercase tracking-wider text-stone">
                  Phone
                </span>
                <input
                  name="phone"
                  type="tel"
                  defaultValue={user.phone}
                  placeholder="+998 90 123 45 67"
                  className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition placeholder:text-stone focus:border-blossom"
                />
              </label>

              <label className="block">
                <span className="text-sm font-bold uppercase tracking-wider text-stone">
                  Email
                </span>
                <input
                  value={user.email}
                  readOnly
                  className="mt-2 w-full rounded-2xl border border-line bg-[#f2f3f7] px-4 py-3 text-sm font-medium text-stone outline-none"
                />
              </label>

              <label className="block">
                <span className="text-sm font-bold uppercase tracking-wider text-stone">
                  Interface language
                </span>
                <select
                  name="language"
                  value={language}
                  onChange={(event) => setLanguage(event.target.value as Language)}
                  className="mt-2 w-full cursor-pointer rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
                >
                  {languages.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              {profileError && (
                <p className="rounded-2xl bg-berrysoft px-4 py-3 text-sm font-semibold text-berry sm:col-span-2">
                  {profileError}
                </p>
              )}

              <button
                type="submit"
                disabled={profileSaving}
                className="rounded-full bg-blossomdeep px-6 py-3 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70 sm:col-span-2"
              >
                {profileSaving ? "Saving..." : "Save account"}
              </button>
            </form>
          </section>

          <section className="rounded-[1.75rem] border border-line bg-white p-5 shadow-soft">
            <h2 className="font-display text-2xl font-extrabold text-ink">
              Security
            </h2>
            <form onSubmit={onAdminPasswordSubmit} className="mt-5 grid gap-4">
              <label className="block">
                <span className="text-sm font-bold uppercase tracking-wider text-stone">
                  Current password
                </span>
                <input
                  type="password"
                  value={oldPassword}
                  onChange={(event) => setOldPassword(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
                />
              </label>

              <label className="block">
                <span className="text-sm font-bold uppercase tracking-wider text-stone">
                  New password
                </span>
                <input
                  type="password"
                  minLength={8}
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
                />
              </label>

              <label className="block">
                <span className="text-sm font-bold uppercase tracking-wider text-stone">
                  Confirm new password
                </span>
                <input
                  type="password"
                  minLength={8}
                  value={newPasswordConfirm}
                  onChange={(event) => setNewPasswordConfirm(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
                />
              </label>

              {passwordError && (
                <p className="rounded-2xl bg-berrysoft px-4 py-3 text-sm font-semibold text-berry">
                  {passwordError}
                </p>
              )}

              <button
                type="submit"
                disabled={passwordSaving}
                className="rounded-full bg-ink px-6 py-3 text-sm font-extrabold text-white shadow-soft transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70"
              >
                {passwordSaving ? "Updating..." : "Change password"}
              </button>
            </form>
          </section>
        </div>
      </section>
    </main>
  );
}

function AuthCard({ initialMode }: { initialMode: AuthMode }) {
  const { language, currency, city, setUser, setName, showToast } = useStore();
  const t = copy[language].auth;
  const router = useRouter();
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const isRegister = mode === "register";

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (isRegister && password !== passwordConfirm) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setSubmitting(true);
      const user = isRegister
        ? await apiRegister({
            username,
            email,
            password,
            password_confirm: passwordConfirm,
            phone: phone || undefined,
            city,
            language,
            currency,
          })
        : await apiLogin(email, password);

      setUser(user);
      setName(user.username);
      showToast(isRegister ? t.successRegister : t.successLogin);
      router.push("/");
    } catch (err) {
      setError(firstApiMessage(err, t.offline));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-[calc(100vh-66px)] bg-gradient-to-br from-[#ffe8f3] via-[#fff3f8] to-white px-5 py-6">
      <section className="mx-auto max-w-[520px] rounded-[28px] border border-line bg-white px-6 py-7 shadow-[0_24px_80px_-45px_rgba(236,22,130,0.7)] sm:px-10 sm:py-8">
        <div className="text-center">
          <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-blush font-display text-2xl font-extrabold text-blossomdeep">
            B
          </div>
          <h1 className="mt-4 font-display text-3xl font-extrabold leading-tight text-ink">
            {isRegister ? t.createTitle : t.loginTitle}
          </h1>
          <p className="mt-1 text-lg text-stone">
            {isRegister ? t.createSubtitle : t.loginSubtitle}
          </p>
        </div>

        <div className="mt-6 rounded-2xl bg-paper px-4 py-3 text-sm">
          <p className="font-extrabold text-ink">Demo accounts</p>
          <p className="mt-1 font-semibold text-stone">
            Customer: customer@example.com / demo12345
          </p>
          <p className="font-semibold text-stone">
            Staff: staff@example.com / demo12345
          </p>
        </div>

        <form onSubmit={onSubmit} className="mt-6 grid gap-4 min-[520px]:grid-cols-2">
          {isRegister && (
            <label className="block">
              <span className="text-sm font-semibold text-ink">
                {t.username} *
              </span>
              <input
                required
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder={t.usernamePlaceholder}
                className="mt-2 w-full rounded-2xl border border-line bg-white px-4 py-3 text-base outline-none transition placeholder:text-stone focus:border-blossomdeep"
              />
            </label>
          )}

          <label className="block">
            <span className="text-sm font-semibold text-ink">{t.email} *</span>
            <input
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder={t.emailPlaceholder}
              className="mt-2 w-full rounded-2xl border border-line bg-white px-4 py-3 text-base outline-none transition placeholder:text-stone focus:border-blossomdeep"
            />
          </label>

          <label className="block min-[520px]:col-span-2">
            <span className="text-sm font-semibold text-ink">
              {t.password} *
            </span>
            <input
              required
              type="password"
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={t.passwordPlaceholder}
                className="mt-2 w-full rounded-2xl border border-line bg-white px-4 py-3 text-base outline-none transition placeholder:text-stone focus:border-blossomdeep"
            />
          </label>

          {isRegister && (
            <>
              <label className="block min-[520px]:col-span-2">
                <span className="text-sm font-semibold text-ink">
                  {t.confirmPassword} *
                </span>
                <input
                  required
                  type="password"
                  minLength={8}
                  value={passwordConfirm}
                  onChange={(event) => setPasswordConfirm(event.target.value)}
                  placeholder={t.confirmPlaceholder}
                  className="mt-2 w-full rounded-2xl border border-line bg-white px-4 py-3 text-base outline-none transition placeholder:text-stone focus:border-blossomdeep"
                />
              </label>

              <label className="block min-[520px]:col-span-2">
                <span className="text-sm font-semibold text-ink">
                  {t.phone} ({t.optional})
                </span>
                <input
                  type="tel"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  placeholder={t.phonePlaceholder}
                  className="mt-2 w-full rounded-2xl border border-line bg-white px-4 py-3 text-base outline-none transition placeholder:text-stone focus:border-blossomdeep"
                />
              </label>
            </>
          )}

          {error && (
              <p className="rounded-2xl bg-berrysoft px-4 py-3 text-sm font-semibold text-berry min-[520px]:col-span-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-2 rounded-full bg-blossomdeep px-6 py-3.5 text-base font-extrabold text-white shadow-glow transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70 min-[520px]:col-span-2"
          >
            {submitting ? "..." : isRegister ? t.createButton : t.loginButton}
          </button>
        </form>

        <p className="mt-5 text-center text-base text-stone">
          {isRegister ? t.haveAccount : t.needAccount}{" "}
          <button
            type="button"
            onClick={() => {
              setError("");
              setMode(isRegister ? "login" : "register");
              router.replace(isRegister ? "/profile?mode=login" : "/profile");
            }}
            className="font-extrabold text-blossomdeep transition hover:text-raspberry"
          >
            {isRegister ? t.signIn : t.signUp}
          </button>
        </p>
      </section>
    </main>
  );
}

function CustomerOrderHistory({ currency }: { currency: Currency }) {
  const { showToast, reloadCart } = useStore();
  const [orders, setOrders] = useState<ApiOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [repeatingId, setRepeatingId] = useState<number | null>(null);
  const [testPayingId, setTestPayingId] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    async function loadOrders() {
      try {
        setLoading(true);
        const data = await fetchOrders();
        if (active) {
          setOrders(data);
          setError("");
        }
      } catch (err) {
        if (active) setError(firstApiMessage(err, "Could not load orders."));
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadOrders();
    return () => {
      active = false;
    };
  }, []);

  async function onRepeatOrder(orderId: number) {
    setError("");
    try {
      setRepeatingId(orderId);
      const result = await repeatOrder(orderId);
      await reloadCart();
      const skipped = result.skipped.length ? ` (${result.skipped.length} skipped)` : "";
      showToast(`Added ${result.cart.total_items} item(s) to cart${skipped}`);
    } catch (err) {
      setError(firstApiMessage(err, "Could not repeat this order."));
    } finally {
      setRepeatingId(null);
    }
  }

  async function onPayTestOrder(orderId: number) {
    setError("");
    try {
      setTestPayingId(orderId);
      const updated = await payTestOrder(orderId);
      setOrders((current) =>
        current.map((order) => (order.id === updated.id ? updated : order)),
      );
      showToast(`Order #${updated.id} paid`);
    } catch (err) {
      setError(
        firstApiMessage(
          err,
          "Could not complete this test payment. Please try again.",
        ),
      );
    } finally {
      setTestPayingId(null);
    }
  }

  return (
    <section className="mt-10 rounded-3xl bg-card p-6 shadow-soft">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl font-semibold sm:text-3xl">
            Order history
          </h2>
          <p className="mt-1 text-sm text-stone">
            Orders created from your Bloom &amp; Petal cart.
          </p>
        </div>
        {orders.length > 0 && (
          <span className="rounded-full bg-mint px-3 py-1 text-xs font-extrabold text-leaf">
            {orders.length} orders
          </span>
        )}
      </div>

      {error && (
        <p className="mt-5 rounded-2xl bg-berrysoft px-4 py-3 text-sm font-semibold text-berry">
          {error}
        </p>
      )}

      {loading ? (
        <LoadingRows label="Loading customer orders" />
      ) : orders.length === 0 ? (
        <EmptyPanel
          title="No orders yet"
          text="Completed checkouts will appear here with delivery timeline and payment status."
          action={
            <Link
              href="/#catalog"
              className="inline-flex rounded-full bg-blossomdeep px-5 py-2.5 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry"
            >
              Browse flowers
            </Link>
          }
        />
      ) : (
        <div className="mt-5 grid gap-3">
          {orders.map((order) => {
            const total = Number.parseFloat(order.total_price);
            const subtotal = Number.parseFloat(order.subtotal_price) || 0;
            const deliveryFee = Number.parseFloat(order.delivery_fee) || 0;
            const mapUrl = deliveryMapUrl(order);
            const canPayTest =
              order.payment_provider === "test" &&
              (order.payment_method === "card" ||
                order.payment_method === "online") &&
              order.payment_status === "pending";
            return (
              <article
                key={order.id}
                className="rounded-3xl border border-line bg-paper p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-display text-xl font-bold">
                      Order #{order.id}
                    </p>
                    <p className="mt-1 text-xs font-semibold text-stone">
                      {formatAdminTime(order.created_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="flex flex-wrap justify-end gap-1.5">
                      <span className={`${badgeBase} ${orderStatusBadgeClass(order.status)}`}>
                        {order.status_display}
                      </span>
                      <span className={`${badgeBase} bg-white text-stone ring-1 ring-line`}>
                        {order.payment_method_display}
                      </span>
                      <span className={`${badgeBase} ${paymentStatusBadgeClass(order.payment_status)}`}>
                        {order.payment_status_display}
                      </span>
                    </div>
                    <p className="mt-2 font-display text-lg font-bold">
                      {formatPrice(Number.isFinite(total) ? total : 0, currency)}
                    </p>
                  </div>
                </div>

                <OrderStatusTimeline steps={order.status_timeline} />

                <ul className="mt-4 grid gap-2">
                  {order.items.map((item) => (
                    <li
                      key={item.id}
                      className="flex items-center justify-between gap-3 text-sm"
                    >
                      <span className="min-w-0 truncate font-semibold">
                        {item.quantity} x {item.product_name}
                      </span>
                      <span className="shrink-0 font-bold text-ink/80">
                        {formatPrice(
                          Number.parseFloat(item.subtotal) || 0,
                          currency,
                        )}
                      </span>
                    </li>
                  ))}
                </ul>

                <div className="mt-4 grid gap-3 rounded-2xl bg-white p-4 text-sm md:grid-cols-4">
                  <div>
                    <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                      Delivery
                    </p>
                    <p className="mt-1 font-bold text-ink">
                      {formatDeliveryDate(order.delivery_date)}
                    </p>
                    <p className="text-stone">
                      {order.delivery_time_slot_display || order.delivery_time_slot}
                    </p>
                    <p className="mt-1 text-stone">
                      {order.delivery_zone?.name || "No zone selected"}
                    </p>
                    <p className="mt-1 text-stone">
                      {order.city_name || "No city"}
                    </p>
                    {order.delivery_requires_confirmation && (
                      <p className="mt-1 text-xs font-bold text-[#9a6410]">
                        Staff will confirm this delivery zone.
                      </p>
                    )}
                  </div>
                  <div>
                    <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                      Recipient
                    </p>
                    <p className="mt-1 font-bold text-ink">
                      {order.recipient_name || "Not provided"}
                    </p>
                    <p className="text-stone">
                      {order.recipient_phone || order.phone}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                      Payment
                    </p>
                    <p className="mt-1 font-bold text-ink">
                      {order.payment_method_display}
                    </p>
                    <p className="text-stone">
                      {order.payment_status_display}
                    </p>
                    {order.payment_provider === "test" && order.payment_reference && (
                      <p className="mt-1 text-xs font-bold text-stone">
                        Test ref {order.payment_reference}
                      </p>
                    )}
                    {order.paid_at && (
                      <p className="mt-1 text-xs font-bold text-leaf">
                        Paid {formatAdminTime(order.paid_at)}
                      </p>
                    )}
                    {canPayTest && (
                      <div className="mt-3 rounded-2xl border border-line bg-paper p-3">
                        <p className="text-xs font-bold text-ink">
                          This is a test payment. No real money will be charged.
                        </p>
                        <button
                          type="button"
                          disabled={testPayingId === order.id}
                          onClick={() => void onPayTestOrder(order.id)}
                          className="mt-2 w-full rounded-full bg-ink px-4 py-2 text-xs font-extrabold text-white transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70"
                        >
                          {testPayingId === order.id
                            ? "Paying..."
                            : "Pay test order"}
                        </button>
                      </div>
                    )}
                  </div>
                  <div>
                    <p className="text-xs font-extrabold uppercase tracking-wider text-stone">
                      Summary
                    </p>
                    <p className="mt-1 text-stone">
                      Items {formatPrice(subtotal, currency)}
                    </p>
                    <p className="text-stone">
                      Delivery{" "}
                      {deliveryFee === 0 ? "Free" : formatPrice(deliveryFee, currency)}
                    </p>
                    {Number.parseFloat(order.discount_amount) > 0 && (
                      <p className="text-leaf">
                        Discount -{formatPrice(Number.parseFloat(order.discount_amount), currency)}
                      </p>
                    )}
                    {order.loyalty_points_earned > 0 && (
                      <p className="text-stone">
                        Earned {order.loyalty_points_earned} points
                      </p>
                    )}
                  </div>
                </div>

                <p className="mt-4 text-sm text-stone">
                  {order.delivery_address || order.shipping_address}
                  {mapUrl && (
                    <a
                      href={mapUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="ml-2 font-extrabold text-blossomdeep hover:text-raspberry"
                    >
                      Open map
                    </a>
                  )}
                </p>
                {order.gift_note && (
                  <p className="mt-2 text-sm font-semibold text-ink">
                    Gift note: {order.gift_note}
                  </p>
                )}
                {order.call_recipient_before_delivery && (
                  <p className="mt-1 text-sm font-semibold text-leaf">
                    Recipient will be called before delivery.
                  </p>
                )}

                <p className="hidden">
                  {order.shipping_address} / {order.phone}
                </p>
                {order.notes && (
                  <p className="mt-1 text-sm text-stone">{order.notes}</p>
                )}
                <button
                  type="button"
                  disabled={repeatingId === order.id}
                  onClick={() => void onRepeatOrder(order.id)}
                  className="mt-4 rounded-full border border-line px-5 py-2.5 text-sm font-extrabold text-stone transition hover:border-blossomdeep hover:text-blossomdeep disabled:cursor-wait disabled:opacity-60"
                >
                  {repeatingId === order.id ? "Adding..." : "Repeat order"}
                </button>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default function ProfileSettings({
  initialMode = "register",
}: {
  initialMode?: AuthMode;
}) {
  const {
    user,
    setUser,
    signOut,
    name,
    setName,
    city,
    setCity,
    currency,
    setCurrency,
    language,
    setLanguage,
    favorites,
    showToast,
  } = useStore();
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirm, setNewPasswordConfirm] = useState("");

  const favoriteProducts = fallbackCatalogProducts.filter((p) => favorites.includes(p.id));
  const samplePrice = 49;

  if (!user) return <AuthCard key={initialMode} initialMode={initialMode} />;
  if (user.is_staff) return <AdminWorkspace />;

  async function onProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) return;
    setProfileError("");

    const form = new FormData(event.currentTarget);
    const nextCity = String(form.get("city") || city) as string;
    const nextLanguage = String(form.get("language") || language) as Language;
    const nextCurrency = String(form.get("currency") || currency) as Currency;

    try {
      setProfileSaving(true);
      const updated = await updateProfile({
        username: String(form.get("username") || user.username),
        phone: String(form.get("phone") || ""),
        address: String(form.get("address") || ""),
        bio: String(form.get("bio") || ""),
        city: nextCity,
        language: nextLanguage,
        currency: nextCurrency,
      });
      setUser(updated);
      setName(updated.username);
      setCity(updated.city);
      setLanguage(updated.language);
      setCurrency(updated.currency);
      showToast("Profile updated");
    } catch (err) {
      setProfileError(firstApiMessage(err, "Could not update profile."));
    } finally {
      setProfileSaving(false);
    }
  }

  async function onPasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError("");

    if (newPassword !== newPasswordConfirm) {
      setPasswordError("New passwords do not match.");
      return;
    }

    try {
      setPasswordSaving(true);
      await changePassword({
        old_password: oldPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      });
      setOldPassword("");
      setNewPassword("");
      setNewPasswordConfirm("");
      showToast("Password changed");
    } catch (err) {
      setPasswordError(firstApiMessage(err, "Could not change password."));
    } finally {
      setPasswordSaving(false);
    }
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-10">
      <div className="flex flex-wrap items-center gap-4">
        <span className="grid size-16 place-items-center rounded-full bg-gradient-to-br from-blossom to-raspberry text-white shadow-lift">
          {name ? (
            <span className="font-display text-2xl font-bold">
              {name.trim().charAt(0).toUpperCase()}
            </span>
          ) : (
            <UserIcon className="size-7" />
          )}
        </span>
        <div>
          <h1 className="font-display text-3xl font-bold sm:text-4xl">
            {name ? `Hello, ${name.trim()}!` : "Your profile"}
          </h1>
          <p className="mt-1 text-sm text-stone">
            Preferences are saved on this device.
          </p>
          <p className="mt-2 inline-flex rounded-full bg-mint px-3 py-1 text-xs font-extrabold text-leaf">
            {user.loyalty_points} loyalty points
          </p>
        </div>
        <button
          type="button"
          onClick={signOut}
          className="ml-auto rounded-full border border-line px-5 py-2.5 text-sm font-bold text-stone transition hover:border-blossomdeep hover:text-blossomdeep"
        >
          Sign out
        </button>
      </div>

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        <section className="rounded-3xl bg-card p-6 shadow-soft">
          <h2 className="font-display text-xl font-semibold">Profile settings</h2>
          <p className="mt-1 text-sm text-stone">
            Saved through your Bloom &amp; Petal profile API.
          </p>

          <form onSubmit={onProfileSubmit} className="mt-5 grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="text-sm font-bold uppercase tracking-wider text-stone">
                Your name
              </span>
              <input
                name="username"
                defaultValue={name || user.username}
                placeholder="Flower Lover"
                className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition placeholder:text-stone focus:border-blossom"
              />
            </label>

            <label className="block">
              <span className="text-sm font-bold uppercase tracking-wider text-stone">
                Phone
              </span>
              <input
                name="phone"
                type="tel"
                defaultValue={user.phone}
                placeholder="+998 90 123 45 67"
                className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition placeholder:text-stone focus:border-blossom"
              />
            </label>

            <label className="block">
              <span className="flex items-center gap-1.5 text-sm font-bold uppercase tracking-wider text-stone">
                <PinIcon className="size-3.5" />
                Delivery city
              </span>
              <select
                name="city"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="mt-2 w-full cursor-pointer rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
              >
                {cities.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-bold uppercase tracking-wider text-stone">
                Language
              </span>
              <select
                name="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value as Language)}
                className="mt-2 w-full cursor-pointer rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
              >
                {languages.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-bold uppercase tracking-wider text-stone">
                Currency
              </span>
              <select
                name="currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value as Currency)}
                className="mt-2 w-full cursor-pointer rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
              >
                {currencyOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block sm:col-span-2">
              <span className="text-sm font-bold uppercase tracking-wider text-stone">
                Bio
              </span>
              <textarea
                name="bio"
                defaultValue={user.bio ?? ""}
                placeholder="Tell florists about your favorite flowers, colors, or delivery notes."
                rows={3}
                className="mt-2 w-full resize-none rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition placeholder:text-stone focus:border-blossom"
              />
            </label>

            <label className="block sm:col-span-2">
              <span className="text-sm font-bold uppercase tracking-wider text-stone">
                Address
              </span>
              <textarea
                name="address"
                defaultValue={user.address}
                placeholder="Street, building, apartment"
                rows={3}
                className="mt-2 w-full resize-none rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition placeholder:text-stone focus:border-blossom"
              />
            </label>

            {profileError && (
              <p className="rounded-2xl bg-berrysoft px-4 py-3 text-sm font-semibold text-berry sm:col-span-2">
                {profileError}
              </p>
            )}

            <button
              type="submit"
              disabled={profileSaving}
              className="rounded-full bg-blossomdeep px-6 py-3 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70 sm:col-span-2"
            >
              {profileSaving ? "Saving..." : "Save profile"}
            </button>
          </form>
        </section>

        <section className="rounded-3xl bg-card p-6 shadow-soft">
          <h2 className="font-display text-xl font-semibold">Security</h2>
          <p className="mt-1 text-sm text-stone">
            Change your password using the profile password API.
          </p>

          <form onSubmit={onPasswordSubmit} className="mt-5 grid gap-4">
            <label className="block">
              <span className="text-sm font-bold uppercase tracking-wider text-stone">
                Current password
              </span>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
              />
            </label>

            <label className="block">
              <span className="text-sm font-bold uppercase tracking-wider text-stone">
                New password
              </span>
              <input
                type="password"
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
              />
            </label>

            <label className="block">
              <span className="text-sm font-bold uppercase tracking-wider text-stone">
                Confirm new password
              </span>
              <input
                type="password"
                minLength={8}
                value={newPasswordConfirm}
                onChange={(e) => setNewPasswordConfirm(e.target.value)}
                className="mt-2 w-full rounded-2xl border border-line bg-paper px-4 py-3 text-sm font-medium outline-none transition focus:border-blossom"
              />
            </label>

            {passwordError && (
              <p className="rounded-2xl bg-berrysoft px-4 py-3 text-sm font-semibold text-berry">
                {passwordError}
              </p>
            )}

            <button
              type="submit"
              disabled={passwordSaving}
              className="rounded-full bg-ink px-6 py-3 text-sm font-extrabold text-white shadow-soft transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70"
            >
              {passwordSaving ? "Updating..." : "Change password"}
            </button>
          </form>

          <p className="mt-5 rounded-2xl bg-paper px-4 py-3 text-xs leading-relaxed text-stone">
            A bouquet at $49 shows as{" "}
            <span className="font-bold text-ink">{formatPrice(49, currency)}</span>{" "}
            with your current currency. Local UZS estimate:{" "}
            <span className="font-bold text-ink">
              {toUzs(samplePrice).toLocaleString("en-US").replace(/,/g, " ")} so&apos;m
            </span>
            .
          </p>
        </section>
      </div>

      <CustomerOrderHistory currency={currency} />

      <section id="favorites" className="mt-10 scroll-mt-24">
        <div className="flex items-center gap-2.5">
          <HeartIcon filled className="size-6 text-berry" />
          <h2 className="font-display text-2xl font-semibold sm:text-3xl">
            Favorites
          </h2>
          {favoriteProducts.length > 0 && (
            <span className="rounded-full bg-berrysoft px-2.5 py-1 text-xs font-bold text-berry">
              {favoriteProducts.length}
            </span>
          )}
        </div>

        {favoriteProducts.length > 0 ? (
          <div className="mt-5 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
            {favoriteProducts.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        ) : (
          <div className="mt-5 rounded-3xl bg-card py-14 text-center shadow-soft">
            <HeartIcon className="mx-auto size-10 text-line" />
            <p className="mt-3 font-display text-xl font-semibold">
              No favorites yet
            </p>
            <p className="mt-1 text-sm text-stone">
              Tap the heart on any bouquet to keep it here.
            </p>
            <Link
              href="/#catalog"
              className="mt-5 inline-block rounded-full bg-blossomdeep px-6 py-2.5 text-sm font-bold text-white transition hover:bg-raspberry active:scale-95"
            >
              Browse the catalog
            </Link>
          </div>
        )}
      </section>
    </main>
  );
}
