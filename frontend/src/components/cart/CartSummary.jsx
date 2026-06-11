import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useCart } from '../../hooks/useCart';
import { formatPrice } from '../../utils/helpers';
import Button from '../common/Button';

function CartSummary() {
  const { t } = useTranslation();
  const { totalPrice, totalItems } = useCart();
  const navigate = useNavigate();

  const shipping = totalPrice > 50 ? 0 : 5.99;
  const total = parseFloat(totalPrice) + shipping;

  return (
    <div style={{
      background: '#fff',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 2px 12px rgba(233,30,140,0.08)',
    }}>
      <h3 style={{
        fontFamily: "'Playfair Display', serif",
        fontSize: '1.3rem',
        marginBottom: '20px',
      }}>
        {t('summary.title')}
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
        <SummaryRow label={t('summary.items', { count: totalItems })} value={formatPrice(totalPrice)} />
        <SummaryRow
          label={t('summary.shipping')}
          value={shipping === 0 ? t('summary.free') : formatPrice(shipping)}
          valueStyle={{ color: shipping === 0 ? '#4caf50' : '#2d2d2d' }}
        />
        {shipping === 0 && (
          <p style={{ fontSize: '0.8rem', color: '#4caf50' }}>
            {t('summary.qualifyFree')}
          </p>
        )}
        {shipping > 0 && (
          <p style={{ fontSize: '0.8rem', color: '#757575' }}>
            {t('summary.addMore', { amount: formatPrice(50 - parseFloat(totalPrice)) })}
          </p>
        )}
      </div>

      <div style={{
        borderTop: '1px solid #f0e0e6',
        paddingTop: '16px',
        marginBottom: '20px',
      }}>
        <SummaryRow
          label={t('summary.total')}
          value={formatPrice(total)}
          bold
        />
      </div>

      <Button
        fullWidth
        onClick={() => navigate('/checkout')}
      >
        {t('summary.checkout')}
      </Button>
    </div>
  );
}

function SummaryRow({ label, value, bold, valueStyle = {} }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ color: '#4a4a4a', fontWeight: bold ? '700' : '400', fontSize: bold ? '1.05rem' : '0.95rem' }}>
        {label}
      </span>
      <span style={{ fontWeight: bold ? '700' : '600', fontSize: bold ? '1.15rem' : '0.95rem', color: bold ? '#e91e8c' : '#2d2d2d', ...valueStyle }}>
        {value}
      </span>
    </div>
  );
}

export default CartSummary;
