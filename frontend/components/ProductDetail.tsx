"use client";

/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { useState } from "react";
import type { Product } from "@/lib/types";
import { copy } from "@/lib/i18n";
import { stockLimit } from "@/lib/selection-state";
import { usePriceFormatter, useStore } from "@/lib/store";
import BouquetArt from "./BouquetArt";
import ProductReviews from "./ProductReviews";
import { ChevronIcon, HeartIcon, MinusIcon, PlusIcon } from "./icons";
import "./catalog-product.css";

const labels = {
  EN: {
    shop: "Shop flowers",
    add: "Add to bag",
    save: "Save",
    saved: "Saved",
    quantity: "Quantity",
    inStock: "In stock",
    unavailable: "Out of stock",
    left: "available",
    details: "Bouquet details",
    delivery: "Delivery & payment",
    estimate: "Delivery fee and available time slots are confirmed at checkout.",
    payment: "Choose an available delivery zone, date, time and payment method when you check out.",
    info: "View delivery & payment",
    photo: "Photo unavailable",
    demo: "Demo catalog item. Live availability and checkout require a connection to the shop.",
  },
  RU: {
    shop: "Выбрать цветы",
    add: "В корзину",
    save: "Сохранить",
    saved: "Сохранено",
    quantity: "Количество",
    inStock: "В наличии",
    unavailable: "Нет в наличии",
    left: "в наличии",
    details: "О букете",
    delivery: "Доставка и оплата",
    estimate: "Стоимость доставки и доступное время уточняются при оформлении.",
    payment: "Выберите доступную зону, дату, время доставки и способ оплаты при оформлении заказа.",
    info: "Условия доставки и оплаты",
    photo: "Фото недоступно",
    demo: "Демонстрационный товар. Для проверки наличия и оформления нужно подключение к магазину.",
  },
  UZ: {
    shop: "Gullarni tanlash",
    add: "Savatga qo‘shish",
    save: "Saqlash",
    saved: "Saqlandi",
    quantity: "Soni",
    inStock: "Mavjud",
    unavailable: "Mavjud emas",
    left: "mavjud",
    details: "Guldasta haqida",
    delivery: "Yetkazish va to‘lov",
    estimate: "Yetkazish narxi va mavjud vaqtlar buyurtma berishda aniqlanadi.",
    payment: "Buyurtma berishda mavjud hudud, sana, vaqt va to‘lov usulini tanlang.",
    info: "Yetkazish va to‘lov shartlari",
    photo: "Surat mavjud emas",
    demo: "Namoyish mahsuloti. Mavjudlikni tekshirish va buyurtma berish uchun do‘konga ulanish kerak.",
  },
};

export default function ProductDetail({ product }: { product: Product }) {
  const formatPrice = usePriceFormatter();
  const { currency, language, favorites, toggleFavorite, addToCart, showToast } = useStore();
  const t = labels[language];
  const detailCopy = copy[language].detail;
  const [qty, setQty] = useState(1);
  const [failedImage, setFailedImage] = useState<string | null>(null);
  const liked = favorites.includes(product.id);
  const maxQty = stockLimit(product);
  const purchasable = maxQty > 0;
  const selectedQty = Math.max(1, Math.min(qty, maxQty));
  const hasPhoto = product.image && failedImage !== product.image;

  return (
    <main className="site-container flower-product">
      <div className="flower-product-grid">
        <div className="flower-product-media">
          {hasPhoto ? (
            <img
              src={product.image!}
              alt={product.name}
              decoding="async"
              onError={() => setFailedImage(product.image ?? null)}
              className="flower-product-image"
            />
          ) : (
            <>
              <BouquetArt palette={product.palette} className="flower-product-art" />
              <span className="flower-photo-notice">{t.photo}</span>
            </>
          )}
        </div>
        <section aria-labelledby="product-title">
          <nav aria-label={detailCopy.breadcrumb} className="flower-product-breadcrumb">
            <Link href="/#catalog">{t.shop}</Link>
            <span aria-hidden="true">/</span>
            <span>{product.name}</span>
          </nav>
          <h1 id="product-title" className="flower-product-title">
            {product.name}
          </h1>
          <p className="flower-product-vendor">{product.shop}</p>
          <p className="flower-product-price">
            {formatPrice(product.price, currency)}
            {product.oldPrice && <del>{formatPrice(product.oldPrice, currency)}</del>}
          </p>
          <p className={`flower-product-stock ${!purchasable ? "flower-stock-unavailable" : ""}`}>
            {purchasable ? t.inStock : t.unavailable}
            {purchasable && typeof product.stock === "number" && (
              <span className="flower-product-stock-count">
                {" "}
                · {product.stock} {t.left}
              </span>
            )}
          </p>
          {product.source === "mock" && <p className="flower-notice">{t.demo}</p>}
          <p className="flower-product-description">{product.description}</p>

          <div className="flower-purchase">
            <p id="quantity-label" className="ui-label">
              {t.quantity}
            </p>
            <div className="flower-quantity" role="group" aria-labelledby="quantity-label">
              <button
                type="button"
                aria-label={detailCopy.qtyDecrease}
                disabled={!purchasable || selectedQty <= 1}
                onClick={() => setQty(Math.max(1, selectedQty - 1))}
              >
                <MinusIcon />
              </button>
              <output aria-live="polite">{selectedQty}</output>
              <button
                type="button"
                aria-label={detailCopy.qtyIncrease}
                disabled={!purchasable || selectedQty >= maxQty}
                onClick={() => setQty(Math.min(maxQty, selectedQty + 1))}
              >
                <PlusIcon />
              </button>
            </div>
            <div className="flower-product-actions">
              <button
                type="button"
                disabled={!purchasable}
                onClick={() => {
                  addToCart(product, selectedQty);
                  showToast(
                    selectedQty === 1
                      ? detailCopy.addedOne.replace("{name}", product.name)
                      : detailCopy.addedMany
                          .replace("{qty}", String(selectedQty))
                          .replace("{name}", product.name),
                  );
                  setQty(1);
                }}
                className="ui-button"
              >
                {purchasable ? t.add : t.unavailable}
                {purchasable && selectedQty > 1
                  ? ` · ${formatPrice(product.price * selectedQty, currency)}`
                  : ""}
              </button>
              <button
                type="button"
                aria-label={liked ? detailCopy.favoriteRemove : detailCopy.favoriteAdd}
                aria-pressed={liked}
                onClick={() => toggleFavorite(product)}
                className="ui-button-secondary"
              >
                <HeartIcon filled={liked} />
                {liked ? t.saved : t.save}
              </button>
            </div>
            <p className="flower-product-delivery">{t.estimate}</p>
          </div>

          <details className="flower-disclosure">
            <summary>
              {t.details}
              <ChevronIcon />
            </summary>
            <div className="flower-disclosure-content">
              <p>{product.description}</p>
              {product.composition.length > 0 && (
                <ul>
                  {product.composition.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
            </div>
          </details>
          <details className="flower-disclosure">
            <summary>
              {t.delivery}
              <ChevronIcon />
            </summary>
            <div className="flower-disclosure-content">
              <p>{t.payment}</p>
              <Link href="/delivery">{t.info}</Link>
            </div>
          </details>
        </section>
      </div>
      <ProductReviews productId={product.id} />
    </main>
  );
}
