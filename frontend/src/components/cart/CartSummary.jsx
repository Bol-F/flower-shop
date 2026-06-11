import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../../hooks/useCart';
import { formatPrice } from '../../utils/helpers';
import Button from '../common/Button';

function CartSummary() {
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
        Order Summary
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
        <SummaryRow label={`Items (${totalItems})`} value={formatPrice(totalPrice)} />
        <SummaryRow
          label="Shipping"
          value={shipping === 0 ? 'Free' : formatPrice(shipping)}
          valueStyle={{ color: shipping === 0 ? '#4caf50' : '#2d2d2d' }}
        />
        {shipping === 0 && (
          <p style={{ fontSize: '0.8rem', color: '#4caf50' }}>
            🎉 You qualify for free shipping!
          </p>
        )}
        {shipping > 0 && (
          <p style={{ fontSize: '0.8rem', color: '#757575' }}>
            Add {formatPrice(50 - parseFloat(totalPrice))} more for free shipping
          </p>
        )}
      </div>

      <div style={{
        borderTop: '1px solid #f0e0e6',
        paddingTop: '16px',
        marginBottom: '20px',
      }}>
        <SummaryRow
          label="Total"
          value={formatPrice(total)}
          bold
        />
      </div>

      <Button
        fullWidth
        onClick={() => navigate('/checkout')}
      >
        Proceed to Checkout →
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
