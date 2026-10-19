"use client";

/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { useState } from "react";
import type { Product } from "@/lib/types";
import { usePriceFormatter, useStore } from "@/lib/store";
import BouquetArt from "./BouquetArt";
import { HeartIcon } from "./icons";
import "./catalog-product.css";

const labels = {
  EN: {
    add: "Add to bag",
    unavailable: "Out of stock",
    delivery: "Delivery at checkout",
    save: "Save",
    unsave: "Remove from saved flowers",
    view: "View",
    added: "added to bag",
    left: "left",
    photo: "Photo unavailable",
  },
  RU: {
    add: "В корзину",
    unavailable: "Нет в наличии",
    delivery: "Доставка при оформлении",
    save: "Сохранить",
    unsave: "Удалить из избранного",
    view: "Смотреть",
    added: "в корзине",
    left: "осталось",
    photo: "Фото недоступно",
  },
  UZ: {
    add: "Savatga qo‘shish",
    unavailable: "Mavjud emas",
    delivery: "Yetkazish buyurtmada",
    save: "Saqlash",
    unsave: "Saqlanganlardan o‘chirish",
    view: "Ko‘rish",
    added: "savatga qo‘shildi",
    left: "qoldi",
    photo: "Surat mavjud emas",
  },
};

export default function ProductCard({ product }: { product: Product }) {
  const [failedImage, setFailedImage] = useState<string | null>(null);
  const formatPrice = usePriceFormatter();
  const { currency, language, favorites, toggleFavorite, addToCart, showToast } = useStore();
  const t = labels[language];
  const liked = favorites.includes(product.id);
  const purchasable =
    product.isAvailable !== false && product.isInStock !== false && product.stock !== 0;
  const lowStock =
    purchasable && typeof product.stock === "number" && product.stock > 0 && product.stock <= 3;
  const hasPhoto = product.image && failedImage !== product.image;

  return (
    <article className="flower-card">
      <div className="flower-card-media">
        <Link
          href={`/product/${product.slug ?? product.id}`}
          aria-label={`${t.view} ${product.name}`}
          className="flower-card-photo-link"
        >
          {hasPhoto ? (
            <img
              src={product.image!}
              alt={product.name}
              loading="lazy"
              decoding="async"
              onError={() => setFailedImage(product.image ?? null)}
              className="flower-card-photo"
            />
          ) : (
            <div className="flower-card-art" style={{ background: product.palette.backdrop }}>
              <BouquetArt palette={product.palette} className="flower-card-bouquet" />
              {product.source === "api" && <span className="flower-photo-notice">{t.photo}</span>}
            </div>
          )}
        </Link>
        <button
          type="button"
          aria-label={`${liked ? t.unsave : t.save}: ${product.name}`}
          aria-pressed={liked}
          onClick={() => toggleFavorite(product)}
          className="flower-card-save"
        >
          <HeartIcon filled={liked} />
        </button>
      </div>
      <div className="flower-card-title-row">
        <h3>
          <Link href={`/product/${product.slug ?? product.id}`}>{product.name}</Link>
        </h3>
        <div className="flower-card-price">
          <span>{formatPrice(product.price, currency)}</span>
          {product.oldPrice && <del>{formatPrice(product.oldPrice, currency)}</del>}
        </div>
      </div>
      <p className="flower-card-meta">{product.shop}</p>
      <p className={`flower-card-meta ${!purchasable ? "flower-stock-unavailable" : ""}`}>
        {!purchasable ? t.unavailable : lowStock ? `${product.stock} ${t.left}` : t.delivery}
      </p>
      <button
        type="button"
        disabled={!purchasable}
        onClick={() => {
          addToCart(product);
          showToast(`${product.name} ${t.added}`);
        }}
        className="ui-button-secondary flower-card-add"
      >
        {purchasable ? t.add : t.unavailable}
      </button>
    </article>
  );
}
