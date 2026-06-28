/**
 * Thin client for the Django REST backend (apps.users + apps.contact).
 * Tokens live in localStorage and are refreshed once on 401, mirroring
 * what SimpleJWT expects. All functions throw ApiError on failure so
 * UI code can show field-level messages from DRF serializers.
 */

function resolveApiBase() {
  const configured = process.env.NEXT_PUBLIC_API_URL;
  if (
    configured &&
    configured !== "http://localhost:8000" &&
    configured !== "http://127.0.0.1:8000"
  ) {
    return configured.replace(/\/$/, "");
  }

  if (typeof window !== "undefined") {
    const { hostname, protocol } = window.location;
    if (hostname !== "localhost" && hostname !== "127.0.0.1") {
      return `${protocol}//${hostname}:8000`;
    }
  }

  return (configured ?? "http://localhost:8000").replace(/\/$/, "");
}

export const API_BASE = resolveApiBase();

const AUTH_KEY = "bloompetal:auth";

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  phone: string;
  address: string;
  bio: string;
  city: string;
  language: "EN" | "RU" | "UZ";
  currency: "USD" | "UZS";
  loyalty_points: number;
  is_staff: boolean;
  date_joined: string;
}

export interface SupportMessage {
  id: number;
  subject: string;
  body: string;
  is_from_admin: boolean;
  admin_reply: string | null;
  replied_at: string | null;
  created_at: string;
}

export interface AdminSupportMessage extends SupportMessage {
  user_email: string;
  user_username: string;
  is_read: boolean;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  image: string | null;
  product_count: number;
}

export interface ApiProductBase {
  id: number;
  name: string;
  slug: string;
  price: string;
  image: string | null;
  category_name: string | null;
  city_name: string | null;
  city_slug: string | null;
  vendor_name: string | null;
  vendor_slug: string | null;
  stock_quantity: number;
  is_available: boolean;
  is_in_stock: boolean;
  is_low_stock: boolean;
  stock_status: "in_stock" | "low_stock" | "out_of_stock" | "unavailable";
}

export interface ApiProductListItem extends ApiProductBase {
  category: number | null;
}

export interface ApiProductDetail extends ApiProductBase {
  description: string;
  category: ApiCategory | null;
  stock: number;
  low_stock_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface ApiCartItem {
  id: number;
  product: ApiProductListItem;
  quantity: number;
  subtotal: string;
}

export interface ApiCart {
  id: number;
  items: ApiCartItem[];
  total_price: string;
  total_items: number;
  updated_at: string;
}

export interface ApiOrderItem {
  id: number;
  product: number | null;
  product_name: string;
  product_price: string;
  quantity: number;
  subtotal: string;
}

export type ApiOrderStatus =
  | "pending"
  | "confirmed"
  | "preparing"
  | "courier_picked_up"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled";

export interface ApiOrderStatusStep {
  id: ApiOrderStatus;
  label: string;
  active: boolean;
  completed: boolean;
}

export type ApiPaymentMethod = "cash" | "card" | "online";
export type ApiPaymentStatus =
  | "unpaid"
  | "pending"
  | "paid"
  | "failed"
  | "refunded";

export interface ApiDeliveryZone {
  id: number;
  name: string;
  city: string;
  city_slug: string;
  fee: string;
  is_active: boolean;
  requires_manual_confirmation: boolean;
  description: string;
}

export interface ApiNotificationLog {
  id: number;
  event: string;
  event_display: string;
  channel: string;
  channel_display: string;
  status: string;
  status_display: string;
  message: string;
  error: string;
  created_at: string;
}

export interface ApiOrder {
  id: number;
  status: ApiOrderStatus;
  status_display: string;
  status_timeline: ApiOrderStatusStep[];
  user_email: string;
  user_username: string;
  city_name: string | null;
  city_slug: string | null;
  vendor_name: string | null;
  vendor_slug: string | null;
  subtotal_price: string;
  total_price: string;
  shipping_address: string;
  phone: string;
  payment_method: ApiPaymentMethod;
  payment_method_display: string;
  payment_status: ApiPaymentStatus;
  payment_status_display: string;
  payment_provider: string;
  payment_reference: string;
  paid_at: string | null;
  promo_code: number | null;
  discount_amount: string;
  loyalty_points_earned: number;
  delivery_address: string;
  delivery_lat: string | null;
  delivery_lng: string | null;
  delivery_date: string | null;
  delivery_time_slot: string;
  delivery_time_slot_display: string;
  delivery_zone: ApiDeliveryZone | null;
  delivery_requires_confirmation: boolean;
  assigned_courier_id: number | null;
  assigned_courier_name: string | null;
  courier_assigned_at: string | null;
  courier_picked_up_at: string | null;
  delivered_at: string | null;
  recipient_name: string;
  recipient_phone: string;
  gift_note: string;
  call_recipient_before_delivery: boolean;
  delivery_fee: string;
  notes: string;
  items: ApiOrderItem[];
  notification_logs: ApiNotificationLog[];
  created_at: string;
  updated_at: string;
}

export interface ApiAdminProductSummary {
  id: number;
  name: string;
  slug: string;
  stock: number;
  low_stock_threshold: number;
  is_available: boolean;
  stock_status: ApiProductBase["stock_status"];
}

export interface ApiBestSellingProduct {
  product_name: string;
  quantity_sold: number;
  revenue: string;
}

export interface ApiCity {
  id: number;
  name: string;
  slug: string;
  country: string;
  currency: "UZS" | "USD";
  is_active: boolean;
  default_delivery_fee: string;
  free_delivery_threshold: string;
}

export interface ApiCourier {
  id: number;
  user: number;
  user_email: string;
  user_username: string;
  phone: string;
  city: ApiCity | null;
  is_active: boolean;
  current_status: "available" | "busy" | "offline";
  created_at: string;
}

export interface ApiDashboardCount {
  status?: string;
  payment_status?: string;
  city?: string;
  count: number;
}

export interface ApiRevenueByDay {
  date: string | null;
  revenue: string;
  orders: number;
}

export interface ApiTopCustomer {
  email: string;
  username: string;
  orders: number;
  revenue: string;
}

export interface ApiAdminDashboard {
  today_orders: number;
  pending_orders: number;
  confirmed_orders: number;
  preparing_orders: number;
  delivered_orders: number;
  total_revenue_today: string;
  total_revenue_month: string;
  low_stock_products: ApiAdminProductSummary[];
  out_of_stock_products: ApiAdminProductSummary[];
  unavailable_products: ApiAdminProductSummary[];
  best_selling_products: ApiBestSellingProduct[];
  revenue_by_day: ApiRevenueByDay[];
  orders_by_status: ApiDashboardCount[];
  payment_status_summary: ApiDashboardCount[];
  city_order_summary: ApiDashboardCount[];
  top_customers: ApiTopCustomer[];
  delivery_queue: ApiOrder[];
}

interface StoredAuth {
  access: string;
  refresh: string;
  user: AuthUser;
}

export class ApiError extends Error {
  /** DRF error payload, e.g. {email: ["..."], password: ["..."]} */
  details: Record<string, unknown>;
  status: number;

  constructor(status: number, details: Record<string, unknown>) {
    super(
      typeof details.detail === "string"
        ? details.detail
        : `Request failed (${status})`,
    );
    this.status = status;
    this.details = details;
  }
}

/** thrown when the backend can't be reached at all */
export class OfflineError extends Error {
  constructor() {
    super("Can't reach the server. Is the backend running?");
  }
}

export function loadAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? (JSON.parse(raw) as StoredAuth) : null;
  } catch {
    return null;
  }
}

function saveAuth(auth: StoredAuth | null) {
  if (auth) localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
  else localStorage.removeItem(AUTH_KEY);
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; auth?: boolean } = {},
): Promise<T> {
  const { method = "GET", body, auth = false } = options;

  const doFetch = async (access?: string) => {
    try {
      return await fetch(`${API_BASE}${path}`, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...(access ? { Authorization: `Bearer ${access}` } : {}),
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch {
      throw new OfflineError();
    }
  };

  let stored = auth ? loadAuth() : null;
  let res = await doFetch(stored?.access);

  // expired access token → refresh once and retry
  if (res.status === 401 && stored?.refresh) {
    const refreshRes = await doFetch_refresh(stored.refresh);
    if (refreshRes) {
      stored = { ...stored, access: refreshRes };
      saveAuth(stored);
      res = await doFetch(stored.access);
    } else {
      saveAuth(null);
    }
  }

  if (!res.ok) {
    let details: Record<string, unknown> = {};
    try {
      details = await res.json();
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, details);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

async function doFetch_refresh(refresh: string): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/api/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { access: string };
    return data.access;
  } catch {
    return null;
  }
}

/* ── auth ─────────────────────────────────────────────────────── */

export async function login(email: string, password: string): Promise<AuthUser> {
  const data = await request<{ access: string; refresh: string; user: AuthUser }>(
    "/api/auth/login/",
    { method: "POST", body: { email, password } },
  );
  saveAuth({ access: data.access, refresh: data.refresh, user: data.user });
  return data.user;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  phone?: string;
  address?: string;
  bio?: string;
  city?: string;
  language?: "EN" | "RU" | "UZ";
  currency?: "USD" | "UZS";
}

export async function register(payload: RegisterPayload): Promise<AuthUser> {
  await request("/api/auth/register/", { method: "POST", body: payload });
  // the register endpoint returns no tokens — log in right after
  return login(payload.email, payload.password);
}

export function logout() {
  saveAuth(null);
}

export async function fetchProfile(): Promise<AuthUser> {
  const user = await request<AuthUser>("/api/auth/profile/", { auth: true });
  const stored = loadAuth();
  if (stored) saveAuth({ ...stored, user });
  return user;
}

export async function updateProfile(
  patch: Partial<
    Pick<
      AuthUser,
      "username" | "phone" | "address" | "bio" | "city" | "language" | "currency"
    >
>,
): Promise<AuthUser> {
  const user = await request<AuthUser>("/api/auth/profile/", {
    method: "PATCH",
    body: patch,
    auth: true,
  });
  const stored = loadAuth();
  if (stored) saveAuth({ ...stored, user });
  return user;
}

export async function changePassword(payload: {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}): Promise<void> {
  await request<void>("/api/auth/profile/password/", {
    method: "POST",
    body: payload,
    auth: true,
  });
}

/* ── support chat (apps.contact) ──────────────────────────────── */

export async function fetchMyMessages(): Promise<SupportMessage[]> {
  const data = await request<SupportMessage[] | { results: SupportMessage[] }>(
    "/api/contact/my-messages/",
    { auth: true },
  );
  return Array.isArray(data) ? data : data.results;
}

export async function sendSupportMessage(body: string): Promise<SupportMessage> {
  // the model wants a subject — derive it from the message itself
  const subject = body.length > 60 ? `${body.slice(0, 57)}…` : body;
  return request<SupportMessage>("/api/contact/send/", {
    method: "POST",
    body: { subject, body },
    auth: true,
  });
}

export async function fetchAdminSupportMessages(): Promise<AdminSupportMessage[]> {
  const data = await request<
    AdminSupportMessage[] | { results: AdminSupportMessage[] }
  >("/api/contact/admin/messages/?page_size=100", { auth: true });
  return Array.isArray(data) ? data : data.results;
}

export async function sendAdminSupportMessage(
  id: number,
  body: string,
): Promise<AdminSupportMessage> {
  return request<AdminSupportMessage>(`/api/contact/admin/messages/${id}/reply/`, {
    method: "POST",
    body: { body },
    auth: true,
  });
}

export async function markSupportMessageRead(id: number): Promise<AdminSupportMessage> {
  return request<AdminSupportMessage>(`/api/contact/admin/messages/${id}/`, {
    method: "PATCH",
    body: { is_read: true },
    auth: true,
  });
}

/* ── catalog, cart & orders ───────────────────────────────────── */

export async function fetchCategories(): Promise<ApiCategory[]> {
  const data = await request<ApiCategory[] | PaginatedResponse<ApiCategory>>(
    "/api/categories/?page_size=100",
  );
  return Array.isArray(data) ? data : data.results;
}

export async function fetchCities(): Promise<ApiCity[]> {
  const data = await request<ApiCity[] | PaginatedResponse<ApiCity>>(
    "/api/marketplace/cities/?page_size=100",
  );
  return Array.isArray(data) ? data : data.results;
}

export async function fetchProducts(params: {
  search?: string;
  category?: string | null;
  city?: string | null;
  vendor?: string | null;
  ordering?: string;
  page_size?: number;
} = {}): Promise<ApiProductListItem[]> {
  const query = new URLSearchParams();
  query.set("page_size", String(params.page_size ?? 100));
  if (params.search) query.set("search", params.search);
  if (params.category) query.set("category", params.category);
  if (params.city) query.set("city", params.city);
  if (params.vendor) query.set("vendor", params.vendor);
  if (params.ordering) query.set("ordering", params.ordering);

  const data = await request<
    ApiProductListItem[] | PaginatedResponse<ApiProductListItem>
  >(`/api/products/?${query.toString()}`);
  return Array.isArray(data) ? data : data.results;
}

export async function fetchProduct(slug: string): Promise<ApiProductDetail> {
  return request<ApiProductDetail>(`/api/products/${encodeURIComponent(slug)}/`);
}

export async function fetchDeliveryZones(city?: string | null): Promise<ApiDeliveryZone[]> {
  const query = new URLSearchParams();
  query.set("page_size", "100");
  if (city) query.set("city", city);
  const data = await request<ApiDeliveryZone[] | PaginatedResponse<ApiDeliveryZone>>(
    `/api/orders/delivery-zones/?${query.toString()}`,
  );
  return Array.isArray(data) ? data : data.results;
}

export async function fetchCouriers(): Promise<ApiCourier[]> {
  const data = await request<ApiCourier[] | PaginatedResponse<ApiCourier>>(
    "/api/marketplace/couriers/?page_size=100",
    { auth: true },
  );
  return Array.isArray(data) ? data : data.results;
}

export async function validatePromoCode(payload: {
  code: string;
  subtotal: string;
}): Promise<{
  code: string;
  discount_type: "fixed_amount" | "percent";
  discount_value: string;
  discount_amount: string;
}> {
  return request("/api/marketplace/promo-codes/validate/", {
    method: "POST",
    body: payload,
  });
}

export async function fetchCart(): Promise<ApiCart> {
  return request<ApiCart>("/api/cart/", { auth: true });
}

export async function addCartItem(productId: number, quantity = 1): Promise<ApiCart> {
  return request<ApiCart>("/api/cart/items/", {
    method: "POST",
    body: { product_id: productId, quantity },
    auth: true,
  });
}

export async function updateCartItem(
  productId: number,
  quantity: number,
): Promise<ApiCart> {
  return request<ApiCart>(`/api/cart/items/${productId}/`, {
    method: "PATCH",
    body: { quantity },
    auth: true,
  });
}

export async function removeCartItem(productId: number): Promise<void> {
  await request<void>(`/api/cart/items/${productId}/`, {
    method: "DELETE",
    auth: true,
  });
}

export async function clearRemoteCart(): Promise<void> {
  await request<void>("/api/cart/", { method: "DELETE", auth: true });
}

export async function createOrder(payload: {
  shipping_address: string;
  phone: string;
  payment_method: ApiPaymentMethod;
  delivery_address?: string;
  delivery_lat?: number | null;
  delivery_lng?: number | null;
  delivery_date?: string;
  delivery_time_slot?: string;
  delivery_zone_id?: number | null;
  city_slug?: string;
  promo_code?: string;
  recipient_name?: string;
  recipient_phone?: string;
  gift_note?: string;
  call_recipient_before_delivery?: boolean;
  notes?: string;
}): Promise<ApiOrder> {
  return request<ApiOrder>("/api/orders/create/", {
    method: "POST",
    body: payload,
    auth: true,
  });
}

export async function fetchOrders(): Promise<ApiOrder[]> {
  const data = await request<ApiOrder[] | PaginatedResponse<ApiOrder>>(
    "/api/orders/?page_size=100",
    { auth: true },
  );
  return Array.isArray(data) ? data : data.results;
}

export async function repeatOrder(id: number): Promise<{
  cart: ApiCart;
  added: Array<{ product: string; quantity: number }>;
  skipped: string[];
}> {
  return request(`/api/orders/${id}/repeat/`, {
    method: "POST",
    body: {},
    auth: true,
  });
}

export async function updateOrderStatus(
  id: number,
  orderStatus: ApiOrderStatus,
): Promise<ApiOrder> {
  return request<ApiOrder>(`/api/orders/${id}/status/`, {
    method: "PATCH",
    body: { status: orderStatus },
    auth: true,
  });
}

export async function updatePaymentStatus(
  id: number,
  paymentStatus: ApiPaymentStatus,
  metadata: { payment_provider?: string; payment_reference?: string } = {},
): Promise<ApiOrder> {
  return request<ApiOrder>(`/api/orders/${id}/payment-status/`, {
    method: "PATCH",
    body: { payment_status: paymentStatus, ...metadata },
    auth: true,
  });
}

export async function assignCourier(
  id: number,
  courierId: number | null,
): Promise<ApiOrder> {
  return request<ApiOrder>(`/api/orders/${id}/courier/`, {
    method: "PATCH",
    body: { courier_id: courierId },
    auth: true,
  });
}

export async function fetchAdminDashboard(): Promise<ApiAdminDashboard> {
  return request<ApiAdminDashboard>("/api/orders/dashboard/", { auth: true });
}

export async function fetchWishlist(): Promise<ApiCartItem["product"][]> {
  const data = await request<
    Array<{ product: ApiProductListItem }> | PaginatedResponse<{ product: ApiProductListItem }>
  >("/api/marketplace/wishlist/?page_size=100", { auth: true });
  const items = Array.isArray(data) ? data : data.results;
  return items.map((item) => item.product);
}

export async function addWishlistItem(productId: number): Promise<void> {
  await request("/api/marketplace/wishlist/", {
    method: "POST",
    body: { product_id: productId },
    auth: true,
  });
}

export async function removeWishlistItem(productId: number): Promise<void> {
  await request<void>(`/api/marketplace/wishlist/${productId}/`, {
    method: "DELETE",
    auth: true,
  });
}

/* ── reviews, ratings & likes (apps.reviews) ──────────────────── */

export interface ReviewItem {
  id: number;
  author: string;
  rating: number;
  body: string;
  created_at: string;
  is_mine: boolean;
}

/** One payload with everything the product page needs. */
export interface ProductSocial {
  product: string;
  rating_average: number | null;
  rating_count: number;
  my_review: { rating: number; body: string } | null;
  reviews: ReviewItem[];
}

/** Public summary; sends the token when signed in so my_review fills in. */
export async function fetchProductSocial(productId: string): Promise<ProductSocial> {
  return request<ProductSocial>(`/api/reviews/products/${productId}/`, {
    auth: true,
  });
}

/** Create or update the signed-in user's review; returns the refreshed summary. */
export async function submitReview(
  productId: string,
  payload: { rating: number; body: string },
): Promise<ProductSocial> {
  return request<ProductSocial>(`/api/reviews/products/${productId}/review/`, {
    method: "POST",
    body: payload,
    auth: true,
  });
}

/** Remove the signed-in user's own review; returns the refreshed summary. */
export async function deleteMyReview(productId: string): Promise<ProductSocial> {
  return request<ProductSocial>(`/api/reviews/products/${productId}/review/`, {
    method: "DELETE",
    auth: true,
  });
}
