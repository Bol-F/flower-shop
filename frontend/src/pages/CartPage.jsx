import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useCart } from '../hooks/useCart';
import CartItem from '../components/cart/CartItem';
import CartSummary from '../components/cart/CartSummary';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Button from '../components/common/Button';

function CartPage() {
  const { t } = useTranslation();
  const { cart, loading, emptyCart } = useCart();

  if (loading) return <LoadingSpinner message={t('cart.loading')} />;

  const items = cart?.items || [];

  return (
    <div className="page-wrapper">
      <div className="container">
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: '2.2rem',
          marginBottom: '32px',
        }}>
          {t('cart.title')}
          {items.length > 0 && (
            <span style={{ fontSize: '1rem', color: '#757575', fontFamily: 'Inter, sans-serif', marginLeft: '12px' }}>
              ({t('common.itemCount', { count: items.length })})
            </span>
          )}
        </h1>

        {items.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: '5rem', marginBottom: '20px' }}>🛒</div>
            <h3>{t('cart.empty')}</h3>
            <p style={{ marginBottom: '32px' }}>{t('cart.emptyHint')}</p>
            <Link to="/products">
              <Button>{t('cart.browse')}</Button>
            </Link>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 360px',
            gap: '32px',
            alignItems: 'start',
          }}>
            {/* Cart Items */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {items.map((item) => (
                <CartItem key={item.id} item={item} />
              ))}

              <div style={{ marginTop: '8px' }}>
                <Button
                  variant="ghost"
                  onClick={emptyCart}
                  style={{ color: '#f44336', fontSize: '0.875rem' }}
                >
                  {t('cart.clear')}
                </Button>
              </div>
            </div>

            {/* Summary */}
            <div style={{ position: 'sticky', top: '90px' }}>
              <CartSummary />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CartPage;
