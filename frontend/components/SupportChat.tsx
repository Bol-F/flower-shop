"use client";

import Link from "next/link";
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
  fetchMyMessages,
  sendSupportMessage,
  type SupportMessage,
} from "@/lib/api";
import { useStore } from "@/lib/store";

const TELEGRAM_URL = "https://t.me/Bol_F";

const text = {
  EN: {
    title: "Support service",
    subtitle: "We usually answer within a few hours",
    loginText: "Sign in to write to support.",
    login: "Sign in",
    telegram: "or message us on Telegram: @Bol_F",
    placeholder: "Write your message...",
    send: "Send",
    empty: "Write your first question. We will answer here.",
    staff: "Staff accounts answer customers from the admin chat.",
    admin: "Open admin chat",
    offline: "Backend is not available.",
    failed: "Could not send the message.",
  },
  RU: {
    title: "Служба поддержки",
    subtitle: "Обычно отвечаем в течение нескольких часов",
    loginText: "Войдите, чтобы написать в поддержку.",
    login: "Войти",
    telegram: "или напишите нам в Telegram: @Bol_F",
    placeholder: "Напишите сообщение...",
    send: "Отправить",
    empty: "Напишите первый вопрос. Ответ появится здесь.",
    staff: "Сотрудники отвечают клиентам в админ-чате.",
    admin: "Открыть админ-чат",
    offline: "Бэкенд недоступен.",
    failed: "Не удалось отправить сообщение.",
  },
  UZ: {
    title: "Yordam xizmati",
    subtitle: "Odatda bir necha soat ichida javob beramiz",
    loginText: "Yordam xizmatiga yozish uchun tizimga kiring.",
    login: "Kirish",
    telegram: "yoki bizga Telegram orqali yozing: @Bol_F",
    placeholder: "Xabaringizni yozing...",
    send: "Yuborish",
    empty: "Birinchi savolingizni yozing. Javob shu yerda chiqadi.",
    staff: "Xodimlar mijozlarga admin chatdan javob beradi.",
    admin: "Admin chatni ochish",
    offline: "Backend ishlamayapti.",
    failed: "Xabar yuborilmadi.",
  },
} as const;

function errorMessage(error: unknown, fallback: string) {
  if (error instanceof OfflineError) return fallback;
  if (error instanceof ApiError) return error.message;
  return error instanceof Error ? error.message : fallback;
}

function timeLabel(value: string | null) {
  if (!value) return "";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

export default function SupportChat() {
  const { user, hydrated, language } = useStore();
  const t = text[language];
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<SupportMessage[]>([]);
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const bodyInputRef = useRef<HTMLTextAreaElement>(null);

  const orderedMessages = useMemo(
    () =>
      [...messages].sort(
        (a, b) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      ),
    [messages],
  );

  useEffect(() => {
    if (!open || !user || user.is_staff) return;

    let cancelled = false;
    async function loadMessages(showSpinner = false) {
      try {
        if (showSpinner) setLoading(true);
        const data = await fetchMyMessages();
        if (!cancelled) {
          setMessages(data);
          setError("");
        }
      } catch (err) {
        if (!cancelled) setError(errorMessage(err, t.offline));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadMessages(true);
    const timer = window.setInterval(() => loadMessages(false), 8000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [open, t.offline, user]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [orderedMessages.length, open]);

  useEffect(() => {
    const input = bodyInputRef.current;
    if (!input) return;
    input.style.height = "0px";
    input.style.height = `${Math.min(input.scrollHeight, 112)}px`;
  }, [body]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = body.trim();
    if (!trimmed || sending) return;

    try {
      setSending(true);
      const sent = await sendSupportMessage(trimmed);
      setMessages((current) => [sent, ...current]);
      setBody("");
      setError("");
    } catch (err) {
      setError(errorMessage(err, t.failed));
    } finally {
      setSending(false);
    }
  }

  function onBodyKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    if (!body.trim() || sending) return;
    event.currentTarget.form?.requestSubmit();
  }

  if (hydrated && user?.is_staff) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 sm:bottom-5 sm:right-6">
      {open && (
        <section className="mb-4 ml-auto flex h-[min(34rem,calc(100vh-7rem))] w-[min(26.5rem,calc(100vw-2.5rem))] animate-fade-up flex-col overflow-hidden rounded-[1.75rem] bg-[#fff8fb] shadow-[0_26px_80px_-34px_rgba(48,43,45,0.45)]">
          <header className="flex items-start justify-between bg-blossomdeep px-5 py-4 text-white">
            <div>
              <h2 className="text-xl font-extrabold leading-tight">
                <span className="mr-2">💬</span>
                {t.title}
              </h2>
              <p className="mt-1 text-sm font-semibold text-white/85">
                {t.subtitle}
              </p>
            </div>
            <button
              type="button"
              aria-label="Close support chat"
              onClick={() => setOpen(false)}
              className="grid size-9 shrink-0 place-items-center rounded-full text-3xl leading-none transition hover:bg-white/15"
            >
              ×
            </button>
          </header>

          {!hydrated || !user ? (
            <div className="grid flex-1 place-items-center px-8 text-center">
              <div>
                <div className="text-5xl">🔐</div>
                <p className="mt-6 text-xl leading-relaxed text-ink">
                  {t.loginText}
                </p>
                <Link
                  href="/profile?mode=login"
                  onClick={() => setOpen(false)}
                  className="mt-5 inline-flex rounded-full bg-blossomdeep px-8 py-3 text-base font-extrabold text-white shadow-glow transition hover:bg-raspberry"
                >
                  {t.login}
                </Link>
                <a
                  href={TELEGRAM_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-5 block text-base font-extrabold text-[#1d9bf0]"
                >
                  {t.telegram}
                </a>
              </div>
            </div>
          ) : user.is_staff ? (
            <div className="grid flex-1 place-items-center px-8 text-center">
              <div>
                <div className="text-5xl">🧑‍💻</div>
                <p className="mt-6 text-lg leading-relaxed text-ink">{t.staff}</p>
                <Link
                  href="/admin"
                  onClick={() => setOpen(false)}
                  className="mt-5 inline-flex rounded-full bg-blossomdeep px-8 py-3 text-base font-extrabold text-white shadow-glow transition hover:bg-raspberry"
                >
                  {t.admin}
                </Link>
              </div>
            </div>
          ) : (
            <>
              <div
                ref={scrollRef}
                className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
              >
                {loading && (
                  <p className="text-center text-sm font-semibold text-stone">...</p>
                )}
                {!loading && orderedMessages.length === 0 && (
                  <p className="mx-auto mt-12 max-w-64 text-center text-sm leading-relaxed text-stone">
                    {t.empty}
                  </p>
                )}
                {orderedMessages.map((message) => (
                  <div key={message.id} className="space-y-2">
                    {message.is_from_admin ? (
                      <div className="max-w-[82%] rounded-[1.15rem] rounded-bl-md bg-white px-4 py-3 text-ink shadow-soft">
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">
                          {message.body}
                        </p>
                        <p className="mt-1 text-[11px] font-semibold text-stone">
                          {timeLabel(message.created_at)}
                        </p>
                      </div>
                    ) : (
                      <>
                        <div className="ml-auto max-w-[82%] rounded-[1.15rem] rounded-br-md bg-blossomdeep px-4 py-3 text-white shadow-soft">
                          <p className="whitespace-pre-wrap text-sm leading-relaxed">
                            {message.body}
                          </p>
                          <p className="mt-1 text-right text-[11px] font-semibold text-white/70">
                            {timeLabel(message.created_at)}
                          </p>
                        </div>
                        {message.admin_reply && (
                          <div className="max-w-[82%] rounded-[1.15rem] rounded-bl-md bg-white px-4 py-3 text-ink shadow-soft">
                            <p className="whitespace-pre-wrap text-sm leading-relaxed">
                              {message.admin_reply}
                            </p>
                            <p className="mt-1 text-[11px] font-semibold text-stone">
                              {timeLabel(message.replied_at)}
                            </p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </div>

              {error && (
                <p className="mx-4 mb-2 rounded-2xl bg-berrysoft px-4 py-2 text-sm font-semibold text-berry">
                  {error}
                </p>
              )}

              <form onSubmit={onSubmit} className="border-t border-line bg-white p-3">
                <div className="flex items-end gap-2">
                  <textarea
                    ref={bodyInputRef}
                    value={body}
                    onChange={(event) => setBody(event.target.value)}
                    onKeyDown={onBodyKeyDown}
                    rows={1}
                    placeholder={t.placeholder}
                    className="max-h-28 min-h-11 flex-1 resize-none overflow-y-auto rounded-[1.35rem] border border-line bg-blush px-4 py-3 text-sm leading-5 outline-none transition placeholder:text-stone focus:border-blossomdeep focus:bg-white"
                  />
                  <button
                    type="submit"
                    disabled={!body.trim() || sending}
                    className="h-11 shrink-0 rounded-full bg-blossomdeep px-5 text-sm font-extrabold text-white shadow-glow transition hover:bg-raspberry disabled:cursor-not-allowed disabled:opacity-55"
                  >
                    {sending ? "..." : t.send}
                  </button>
                </div>
              </form>
            </>
          )}
        </section>
      )}

      <button
        type="button"
        aria-label={open ? "Close support chat" : "Open support chat"}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="ml-auto grid size-14 place-items-center rounded-full border-2 border-ink bg-blossomdeep text-3xl leading-none text-white shadow-[0_16px_44px_-16px_rgba(236,22,130,0.85)] transition hover:-translate-y-1 hover:bg-raspberry active:translate-y-0 sm:size-[68px] sm:text-4xl"
      >
        {open ? "×" : "💬"}
      </button>
    </div>
  );
}
