"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import {
  ApiError,
  OfflineError,
  fetchAdminSupportMessages,
  login as apiLogin,
  markSupportMessageRead,
  sendAdminSupportMessage,
  type AdminSupportMessage,
} from "@/lib/api";
import { useStore } from "@/lib/store";

type Conversation = {
  key: string;
  name: string;
  email: string;
  messages: AdminSupportMessage[];
  lastMessage: AdminSupportMessage;
  unread: number;
};

function firstError(error: unknown, fallback: string) {
  if (error instanceof OfflineError) return "Backend is not available.";
  if (error instanceof ApiError) return error.message;
  return error instanceof Error ? error.message : fallback;
}

function formatChatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function initials(name: string, email: string) {
  const source = name.trim() || email.trim();
  return source.slice(0, 2).toUpperCase();
}

function buildConversations(messages: AdminSupportMessage[]): Conversation[] {
  const grouped = new Map<string, AdminSupportMessage[]>();

  for (const message of messages) {
    const key = message.user_email || `user-${message.id}`;
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
      };
    })
    .sort(
      (a, b) =>
        new Date(b.lastMessage.created_at).getTime() -
        new Date(a.lastMessage.created_at).getTime(),
    );
}

function AdminLogin() {
  const { setUser, setName } = useStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      setSubmitting(true);
      const user = await apiLogin(email, password);
      setUser(user);
      setName(user.username);
      if (!user.is_staff) {
        setError("This account is not an admin account.");
      }
    } catch (err) {
      setError(firstError(err, "Could not sign in."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-[calc(100vh-66px)] bg-[#f7f0f4] px-5 py-10">
      <section className="mx-auto max-w-md rounded-[2rem] bg-white p-8 shadow-lift">
        <p className="text-sm font-extrabold uppercase tracking-[0.18em] text-blossomdeep">
          Admin
        </p>
        <h1 className="mt-2 font-display text-4xl font-extrabold text-ink">
          Support inbox
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-stone">
          Sign in with a staff account to answer customer support chats.
        </p>

        <form onSubmit={onSubmit} className="mt-7 space-y-4">
          <label className="block">
            <span className="text-sm font-bold text-ink">Email</span>
            <input
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-line bg-white px-4 py-3 outline-none transition focus:border-blossomdeep"
            />
          </label>
          <label className="block">
            <span className="text-sm font-bold text-ink">Password</span>
            <input
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-line bg-white px-4 py-3 outline-none transition focus:border-blossomdeep"
            />
          </label>
          {error && (
            <p className="rounded-2xl bg-berrysoft px-4 py-3 text-sm font-bold text-berry">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-full bg-blossomdeep px-6 py-3.5 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry disabled:cursor-wait disabled:opacity-70"
          >
            {submitting ? "Signing in..." : "Open admin chat"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default function AdminSupportInbox() {
  const { user, hydrated } = useStore();
  const [messages, setMessages] = useState<AdminSupportMessage[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const replyInputRef = useRef<HTMLTextAreaElement>(null);

  const conversations = useMemo(() => buildConversations(messages), [messages]);
  const totalMessages = messages.length;
  const selectedConversation =
    conversations.find((conversation) => conversation.key === selectedKey) ??
    conversations[0] ??
    null;
  const replyTarget = selectedConversation?.lastMessage ?? null;

  async function loadMessages(showSpinner = false) {
    try {
      if (showSpinner) setLoading(true);
      const data = await fetchAdminSupportMessages();
      setMessages(data);
      setError("");
    } catch (err) {
      setError(firstError(err, "Could not load support messages."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!hydrated || !user?.is_staff) return;
    const firstLoad = window.setTimeout(() => {
      void loadMessages(true);
    }, 0);
    const timer = window.setInterval(() => loadMessages(false), 7000);
    return () => {
      window.clearTimeout(firstLoad);
      window.clearInterval(timer);
    };
  }, [hydrated, user?.is_staff]);

  useEffect(() => {
    const input = replyInputRef.current;
    if (!input) return;
    input.style.height = "0px";
    input.style.height = `${Math.min(input.scrollHeight, 132)}px`;
  }, [reply]);

  async function selectConversation(conversation: Conversation) {
    setSelectedKey(conversation.key);
    const unread = conversation.messages.filter(
      (message) => !message.is_from_admin && !message.is_read,
    );
    if (unread.length === 0) return;
    setMessages((current) =>
      current.map((message) =>
        unread.some((item) => item.id === message.id)
          ? { ...message, is_read: true }
          : message,
      ),
    );
    await Promise.allSettled(
      unread.map((message) => markSupportMessageRead(message.id)),
    );
  }

  async function onReply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = reply.trim();
    if (!trimmed || !replyTarget || sending) return;

    try {
      setSending(true);
      const sent = await sendAdminSupportMessage(replyTarget.id, trimmed);
      setMessages((current) => [sent, ...current]);
      setReply("");
      setError("");
    } catch (err) {
      setError(firstError(err, "Could not send reply."));
    } finally {
      setSending(false);
    }
  }

  function onReplyKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    if (!reply.trim() || sending) return;
    event.currentTarget.form?.requestSubmit();
  }

  if (!hydrated) {
    return (
      <main className="grid min-h-[calc(100vh-66px)] place-items-center bg-[#f7f0f4]">
        <p className="text-sm font-bold text-stone">Loading...</p>
      </main>
    );
  }

  if (!user) return <AdminLogin />;

  if (!user.is_staff) {
    return (
      <main className="grid min-h-[calc(100vh-66px)] place-items-center bg-[#f7f0f4] px-5 text-center">
        <section className="max-w-md rounded-[2rem] bg-white p-8 shadow-lift">
          <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-blush text-2xl font-extrabold text-blossomdeep">
            !
          </div>
          <h1 className="mt-4 font-display text-3xl font-extrabold text-ink">
            Staff only
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-stone">
            Your account is signed in, but it is not allowed to view customer
            support chats.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-[calc(100vh-66px)] bg-[#f7f0f4] px-4 py-5">
      <section className="mx-auto grid h-[calc(100vh-7.5rem)] max-w-7xl overflow-hidden rounded-[2rem] bg-white shadow-lift lg:grid-cols-[23rem_1fr]">
        <aside className="border-b border-line bg-[#fff8fb] lg:border-b-0 lg:border-r">
          <div className="border-b border-line px-5 py-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-blossomdeep">
                  Admin
                </p>
                <h1 className="font-display text-2xl font-extrabold text-ink">
                  Support chats
                </h1>
                <p className="mt-1 text-xs font-bold text-stone">
                  {conversations.length} chats · {totalMessages} messages
                </p>
              </div>
              <button
                type="button"
                onClick={() => loadMessages(true)}
                className="rounded-full bg-blush px-4 py-2 text-xs font-extrabold text-blossomdeep transition hover:bg-blushdeep"
              >
                Refresh
              </button>
            </div>
            {error && (
              <p className="mt-3 rounded-2xl bg-berrysoft px-3 py-2 text-xs font-bold text-berry">
                {error}
              </p>
            )}
          </div>

          <div className="h-[18rem] overflow-y-auto lg:h-[calc(100%-5.65rem)]">
            {loading && conversations.length === 0 && (
              <div className="grid gap-3 p-5">
                {[0, 1, 2].map((item) => (
                  <div key={item} className="animate-pulse rounded-2xl bg-white p-3">
                    <div className="h-4 w-32 rounded-full bg-line" />
                    <div className="mt-2 h-3 rounded-full bg-line" />
                  </div>
                ))}
              </div>
            )}
            {!loading && conversations.length === 0 && (
              <div className="p-5 text-center">
                <div className="mx-auto grid size-12 place-items-center rounded-2xl bg-blush text-lg font-extrabold text-blossomdeep">
                  0
                </div>
                <p className="mt-3 font-display text-lg font-bold text-ink">
                  No support messages
                </p>
                <p className="mt-1 text-sm leading-relaxed text-stone">
                  New customer support requests will appear here.
                </p>
              </div>
            )}
            {conversations.map((conversation) => {
              const active = selectedConversation?.key === conversation.key;
              return (
                <button
                  key={conversation.key}
                  type="button"
                  onClick={() => selectConversation(conversation)}
                  className={`flex w-full items-center gap-3 border-b border-line px-4 py-3 text-left transition ${
                    active ? "bg-white" : "hover:bg-white/70"
                  }`}
                >
                  <span className="grid size-12 shrink-0 place-items-center rounded-full bg-blossomdeep text-sm font-extrabold text-white">
                    {initials(conversation.name, conversation.email)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-extrabold text-ink">
                        {conversation.name}
                      </span>
                      <span className="shrink-0 text-[11px] font-semibold text-stone">
                        {formatChatTime(conversation.lastMessage.created_at)}
                      </span>
                    </span>
                    <span className="mt-0.5 block truncate text-xs text-stone">
                      {conversation.lastMessage.is_from_admin ? "You: " : ""}
                      {conversation.lastMessage.body}
                    </span>
                  </span>
                  <span className="flex shrink-0 flex-col items-end gap-1">
                    <span className="rounded-full bg-blush px-2 py-0.5 text-[11px] font-extrabold text-blossomdeep">
                      {conversation.messages.length}
                    </span>
                    {conversation.unread > 0 && (
                      <span className="grid size-5 place-items-center rounded-full bg-blossomdeep text-[11px] font-bold text-white">
                        {conversation.unread}
                      </span>
                    )}
                  </span>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="flex min-h-0 flex-col">
          {selectedConversation ? (
            <>
              <header className="flex items-center gap-3 border-b border-line bg-white px-5 py-4">
                <span className="grid size-11 place-items-center rounded-full bg-blossomdeep text-sm font-extrabold text-white">
                  {initials(selectedConversation.name, selectedConversation.email)}
                </span>
                <div className="min-w-0">
                  <h2 className="truncate text-base font-extrabold text-ink">
                    {selectedConversation.name}
                  </h2>
                  <p className="truncate text-xs font-semibold text-stone">
                    {selectedConversation.email}
                  </p>
                </div>
              </header>

              <div className="flex-1 space-y-4 overflow-y-auto bg-[#f9eef4] px-5 py-5">
                {selectedConversation.messages.map((message) => (
                  <div key={message.id} className="space-y-2">
                    {message.is_from_admin ? (
                      <div className="ml-auto max-w-[78%] rounded-[1.15rem] rounded-br-md bg-blossomdeep px-4 py-3 text-white shadow-soft">
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">
                          {message.body}
                        </p>
                        <p className="mt-2 text-right text-[11px] font-semibold text-white/70">
                          {formatChatTime(message.created_at)}
                        </p>
                      </div>
                    ) : (
                      <>
                        <div className="max-w-[78%] rounded-[1.15rem] rounded-bl-md bg-white px-4 py-3 shadow-soft">
                          <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">
                            {message.body}
                          </p>
                          <p className="mt-2 text-[11px] font-semibold text-stone">
                            {formatChatTime(message.created_at)}
                          </p>
                        </div>
                        {message.admin_reply && (
                          <div className="ml-auto max-w-[78%] rounded-[1.15rem] rounded-br-md bg-blossomdeep px-4 py-3 text-white shadow-soft">
                            <p className="whitespace-pre-wrap text-sm leading-relaxed">
                              {message.admin_reply}
                            </p>
                            <p className="mt-2 text-right text-[11px] font-semibold text-white/70">
                              {message.replied_at
                                ? formatChatTime(message.replied_at)
                                : ""}
                            </p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </div>

              <form onSubmit={onReply} className="border-t border-line bg-white p-4">
                <div className="flex items-end gap-3">
                  <textarea
                    ref={replyInputRef}
                    value={reply}
                    onChange={(event) => setReply(event.target.value)}
                    onKeyDown={onReplyKeyDown}
                    rows={1}
                    placeholder={`Message ${selectedConversation.name}`}
                    className="max-h-32 min-h-12 flex-1 resize-none overflow-y-auto rounded-[1.35rem] border border-line bg-blush px-4 py-3 text-sm leading-6 outline-none transition placeholder:text-stone focus:border-blossomdeep focus:bg-white"
                  />
                  <button
                    type="submit"
                    disabled={!reply.trim() || sending}
                    className="h-12 shrink-0 rounded-full bg-blossomdeep px-7 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry disabled:cursor-not-allowed disabled:opacity-55"
                  >
                    {sending ? "Sending..." : "Send"}
                  </button>
                </div>
              </form>
            </>
          ) : (
            <div className="grid flex-1 place-items-center bg-[#f9eef4] text-center">
              <div>
                <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-white text-2xl font-extrabold text-blossomdeep shadow-soft">
                  B
                </div>
                <p className="mt-3 text-sm font-bold text-stone">
                  Choose a chat to start replying.
                </p>
              </div>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
