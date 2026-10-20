"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import {
  askFlowerAdvice,
  fetchAssistantCapabilities,
  type AssistantCapabilities,
  type FlowerAdvice,
} from "@/lib/api";
import { useStore } from "@/lib/store";

const copy = {
  EN: {
    title: "A little help choosing flowers",
    intro: "Tell us the occasion, your budget, or ask about bouquet care.",
    question: "Your question",
    placeholder: "Which bouquet would suit a birthday gift under $60?",
    search: "Search the web for flower-care information",
    ask: "Ask the flower helper",
    working: "Thinking…",
    login: "Sign in to ask a question",
    sources: "Sources",
    privacy:
      "Your question and the public catalog are sent to Google. If you enable web search, your question is also sent to Tavily. Please do not include personal or payment details.",
    warning: "AI can make mistakes. Confirm prices, availability, and delivery at checkout.",
    unavailable: "The flower helper is not available yet. Our support team can help you choose.",
    failed: "We couldn't get flower advice. Please try again, or contact support.",
    retry: "Check again",
    shop: "Back to flowers",
    support: "Contact support",
  },
  RU: {
    title: "Поможем выбрать цветы",
    intro: "Расскажите о поводе, бюджете или задайте вопрос об уходе.",
    question: "Ваш вопрос",
    placeholder: "Какой букет подарить на день рождения до $60?",
    search: "Искать советы по уходу в интернете",
    ask: "Спросить помощника",
    working: "Думаем…",
    login: "Войдите, чтобы задать вопрос",
    sources: "Источники",
    privacy:
      "Ваш вопрос и открытый каталог передаются Google. При включённом поиске вопрос также передаётся Tavily. Не указывайте личные и платёжные данные.",
    warning: "ИИ может ошибаться. Уточняйте цены, наличие и доставку при оформлении заказа.",
    unavailable: "Помощник пока недоступен. Наша поддержка поможет выбрать букет.",
    failed: "Не удалось получить совет. Попробуйте снова или обратитесь в поддержку.",
    retry: "Проверить снова",
    shop: "К цветам",
    support: "Связаться с поддержкой",
  },
  UZ: {
    title: "Gul tanlashda yordam",
    intro: "Tadbir, byudjet yoki gullarni parvarish qilish haqida so‘rang.",
    question: "Savolingiz",
    placeholder: "$60 gacha tug‘ilgan kun uchun qaysi guldasta mos?",
    search: "Gul parvarishi bo‘yicha internetdan izlash",
    ask: "Yordamchidan so‘rash",
    working: "O‘ylayapmiz…",
    login: "Savol berish uchun kiring",
    sources: "Manbalar",
    privacy:
      "Savolingiz va ochiq katalog Google'ga yuboriladi. Internet qidiruvi yoqilsa, savolingiz Tavily'ga ham yuboriladi. Shaxsiy yoki to‘lov ma’lumotlarini kiritmang.",
    warning: "AI xato qilishi mumkin. Narx, mavjudlik va yetkazishni buyurtma vaqtida tekshiring.",
    unavailable: "Yordamchi hali ishlamayapti. Yordam xizmatimiz guldasta tanlashda yordam beradi.",
    failed: "Maslahat olinmadi. Qayta urinib ko‘ring yoki yordam xizmatiga murojaat qiling.",
    retry: "Qayta tekshirish",
    shop: "Gullarga qaytish",
    support: "Yordam xizmatiga yozish",
  },
} as const;

export default function FlowerAssistant() {
  const { user, hydrated, language } = useStore();
  const t = copy[language];
  const [capabilities, setCapabilities] = useState<AssistantCapabilities | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [message, setMessage] = useState("");
  const [useWeb, setUseWeb] = useState(false);
  const [busy, setBusy] = useState(false);
  const [answer, setAnswer] = useState<FlowerAdvice | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    fetchAssistantCapabilities().then(
      (result) => {
        if (active) setCapabilities(result);
      },
      () => {
        if (active) setCapabilities({ enabled: false, web_search_enabled: false });
      },
    );
    return () => {
      active = false;
    };
  }, [attempt]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !message.trim() || !user || !capabilities?.enabled) return;
    setBusy(true);
    setFailed(false);
    setAnswer(null);
    try {
      setAnswer(
        await askFlowerAdvice({
          message: message.trim(),
          language,
          use_web_search: useWeb && capabilities.web_search_enabled,
        }),
      );
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-3xl px-5 py-12 sm:py-16">
      <Link href="/#catalog" className="text-sm font-semibold text-blossomdeep">
        ← {t.shop}
      </Link>
      <p className="mt-8 text-xs font-extrabold uppercase tracking-[0.2em] text-stone">
        Bloom & Petal · AI
      </p>
      <h1 className="mt-3 font-display text-4xl text-ink sm:text-5xl">{t.title}</h1>
      <p className="mt-4 text-lg text-stone">{t.intro}</p>
      {!capabilities ? (
        <p className="mt-8" role="status">
          …
        </p>
      ) : !capabilities.enabled ? (
        <div className="mt-8 rounded-3xl border border-line bg-blush p-6">
          <p>{t.unavailable}</p>
          <div className="mt-5 flex flex-wrap gap-4">
            <a
              href="https://t.me/Bol_F"
              target="_blank"
              rel="noreferrer"
              className="font-semibold text-blossomdeep"
            >
              {t.support}
            </a>
            <button
              type="button"
              onClick={() => {
                setCapabilities(null);
                setAttempt((value) => value + 1);
              }}
              className="font-semibold text-stone"
            >
              {t.retry}
            </button>
          </div>
        </div>
      ) : !hydrated || !user ? (
        <Link
          href="/profile?mode=login"
          className="mt-8 inline-flex rounded-full bg-blossomdeep px-6 py-3 font-bold text-white"
        >
          {t.login}
        </Link>
      ) : (
        <form
          onSubmit={submit}
          className="mt-8 space-y-4 rounded-3xl border border-line bg-card p-5 sm:p-8"
        >
          <label htmlFor="flower-question" className="block font-bold">
            {t.question}
          </label>
          <textarea
            id="flower-question"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            maxLength={1500}
            required
            rows={4}
            disabled={busy}
            placeholder={t.placeholder}
            aria-describedby="assistant-privacy"
            className="w-full resize-y rounded-2xl border border-line p-4 outline-none focus:border-blossomdeep disabled:opacity-60"
          />
          {capabilities.web_search_enabled && (
            <label className="flex items-start gap-3 text-sm">
              <input
                type="checkbox"
                checked={useWeb}
                disabled={busy}
                onChange={(event) => setUseWeb(event.target.checked)}
                className="mt-1 accent-blossomdeep"
              />
              {t.search}
            </label>
          )}
          <p id="assistant-privacy" className="text-xs leading-relaxed text-stone">
            {t.privacy}
          </p>
          <button
            disabled={busy || !message.trim()}
            className="rounded-full bg-blossomdeep px-6 py-3 font-bold text-white disabled:opacity-50"
          >
            {busy ? t.working : t.ask}
          </button>
        </form>
      )}
      {failed && (
        <p role="alert" className="mt-6 rounded-2xl bg-blush p-4 text-berry">
          {t.failed}
        </p>
      )}
      {answer && (
        <section aria-live="polite" className="mt-6 rounded-3xl border border-line p-6">
          <p className="whitespace-pre-wrap leading-relaxed">{answer.answer}</p>
          {answer.sources.length > 0 && (
            <div className="mt-6 space-y-2">
              <h2 className="text-sm font-bold">{t.sources}</h2>
              {answer.sources
                .filter((source) => /^https:\/\//i.test(source.url))
                .map((source, index) => (
                  <a
                    key={`${source.url}-${index}`}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block break-words text-sm text-blossomdeep underline"
                  >
                    {source.title}
                  </a>
                ))}
            </div>
          )}
          <p className="mt-6 text-xs leading-relaxed text-stone">{t.warning}</p>
        </section>
      )}
    </section>
  );
}
