"use client";

import { useStore } from "@/lib/store";
import { BoltIcon, CameraIcon, LeafIcon, TruckIcon } from "./icons";

const descriptions = {
  EN: [
    ["Delivery your way", "Choose an available delivery zone and time at checkout"],
    ["Made for gifting", "Add a recipient and a personal note to your bouquet"],
    ["Clear availability", "See which bouquets are in stock before you order"],
    ["Help when you need it", "Track your orders and reach our support team"],
  ],
  RU: [
    ["Удобная доставка", "Выберите доступную зону и время при оформлении"],
    ["Для ваших подарков", "Укажите получателя и добавьте личное пожелание"],
    ["Понятное наличие", "Проверьте наличие букетов перед заказом"],
    ["Мы на связи", "Следите за заказами и обращайтесь в поддержку"],
  ],
  UZ: [
    ["Qulay yetkazish", "Buyurtmada mavjud hudud va vaqtni tanlang"],
    ["Sovg‘a uchun", "Qabul qiluvchi va shaxsiy tilakni qo‘shing"],
    ["Aniq mavjudlik", "Buyurtmadan oldin guldastalar mavjudligini tekshiring"],
    ["Yordam doim yoningizda", "Buyurtmalarni kuzating va yordam xizmatiga yozing"],
  ],
} as const;

const perks = [
  {
    icon: BoltIcon,
    tint: "bg-blush text-raspberry",
  },
  {
    icon: CameraIcon,
    tint: "bg-berrysoft text-berry",
  },
  {
    icon: LeafIcon,
    tint: "bg-mint text-leaf",
  },
  {
    icon: TruckIcon,
    tint: "bg-lilac text-iris",
  },
];

export default function PerksStrip() {
  const { language } = useStore();
  return (
    <section aria-label="Why Bloom and Petal" className="mx-auto max-w-7xl px-4 py-10">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {perks.map(({ icon: Icon, tint }, index) => (
          <div
            key={index}
            className="group flex items-center gap-4 rounded-3xl bg-card p-5 shadow-soft transition duration-300 hover:-translate-y-1"
          >
            <span
              className={`grid size-12 shrink-0 place-items-center rounded-2xl transition duration-300 group-hover:scale-110 group-hover:-rotate-6 ${tint}`}
            >
              <Icon className="size-5.5" />
            </span>
            <div>
              <p className="text-sm font-bold">{descriptions[language][index][0]}</p>
              <p className="mt-0.5 text-xs leading-snug text-stone">
                {descriptions[language][index][1]}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
