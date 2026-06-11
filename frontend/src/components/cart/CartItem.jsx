import React from 'react';
import { useCart } from '../../hooks/useCart';
import { formatPrice, getImageUrl } from '../../utils/helpers';

function CartItem({ item }) {
  const { updateItem, removeItem } = useCart();

  const handleQuantityChange = async (newQty) => {
    if (newQty < 1) return;
    await updateItem(item.product.id, newQty);
  };

  const handleRemove = async () => {
    await removeItem(item.product.id);
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      padding: '16px',
      background: '#fff',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(233,30,140,0.06)',
    }}>
      {/* Image */}
      <div style={{
        width: '80px',
        height: '80px',
        borderRadius: '10px',
        overflow: 'hidden',
        background: '#fff0f5',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '2.5rem',
        flexShrink: 0,
      }}>
        {item.product.image ? (
          <img
            src={getImageUrl(item.product.image)}
            alt={item.product.name}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : '🌸'}
      </div>

      {/* Details */}
      <div style={{ flex: 1 }}>
        <h4 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: '1rem',
          marginBottom: '4px',
        }}>
          {item.product.name}
        </h4>
        <p style={{ color: '#e91e8c', fontWeight: '600' }}>
          {formatPrice(item.product.price)} each
        </p>
      </div>

      {/* Quantity Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <button
          onClick={() => handleQuantityChange(item.quantity - 1)}
          style={qtyBtnStyle}
        >
          −
        </button>
        <span style={{ fontWeight: '600', minWidth: '24px', textAlign: 'center' }}>
          {item.quantity}
        </span>
        <button
          onClick={() => handleQuantityChange(item.quantity + 1)}
          style={qtyBtnStyle}
        >
          +
        </button>
      </div>

      {/* Subtotal */}
      <div style={{ textAlign: 'right', minWidth: '80px' }}>
        <p style={{ fontWeight: '700', color: '#2d2d2d' }}>
          {formatPrice(item.subtotal)}
        </p>
      </div>

      {/* Remove */}
      <button
        onClick={handleRemove}
        style={{
          color: '#f44336',
          background: 'none',
          border: 'none',
          fontSize: '1.2rem',
          cursor: 'pointer',
          padding: '4px',
        }}
        title="Remove item"
      >
        🗑️
      </button>
    </div>
  );
}

const qtyBtnStyle = {
  width: '32px',
  height: '32px',
  borderRadius: '50%',
  border: '1.5px solid #f0e0e6',
  background: '#fff',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '1rem',
  fontWeight: '600',
  color: '#e91e8c',
};

export default CartItem;
