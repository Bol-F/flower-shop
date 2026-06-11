import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../../hooks/useCart';
import { useAuth } from '../../hooks/useAuth';
import { formatPrice, getImageUrl } from '../../utils/helpers';

function ProductCard({ product }) {
  const { addItem } = useCart();
  const { isAuthenticated } = useAuth();
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  const handleAddToCart = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      window.location.href = '/login';
      return;
    }
    setAdding(true);
    try {
      await addItem(product.id, 1);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } catch {
      // silently fail - cart will show error
    } finally {
      setAdding(false);
    }
  };

  return (
    <Link to={`/products/${product.slug}`} style={{ textDecoration: 'none' }}>
      <div style={{
        background: '#fff',
        borderRadius: '16px',
        overflow: 'hidden',
        boxShadow: '0 2px 12px rgba(233,30,140,0.06)',
        transition: 'transform 0.2s, box-shadow 0.2s',
        cursor: 'pointer',
      }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 8px 30px rgba(233,30,140,0.14)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 2px 12px rgba(233,30,140,0.06)';
        }}
      >
        {/* Image */}
        <div style={{
          height: '220px',
          overflow: 'hidden',
          background: '#fff0f5',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '5rem',
        }}>
          {product.image ? (
            <img
              src={getImageUrl(product.image)}
              alt={product.name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            '🌸'
          )}
        </div>

        {/* Info */}
        <div style={{ padding: '16px' }}>
          {product.category_name && (
            <span style={{
              fontSize: '0.75rem',
              color: '#e91e8c',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}>
              {product.category_name}
            </span>
          )}
          <h3 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: '1.05rem',
            margin: '4px 0 8px',
            color: '#2d2d2d',
          }}>
            {product.name}
          </h3>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{
              fontSize: '1.15rem',
              fontWeight: '700',
              color: '#e91e8c',
            }}>
              {formatPrice(product.price)}
            </span>

            <button
              onClick={handleAddToCart}
              disabled={adding || !product.is_in_stock}
              style={{
                background: added
                  ? '#4caf50'
                  : product.is_in_stock
                  ? 'linear-gradient(135deg, #e91e8c, #c2185b)'
                  : '#ccc',
                color: '#fff',
                border: 'none',
                borderRadius: '20px',
                padding: '8px 16px',
                fontSize: '0.8rem',
                fontWeight: '600',
                cursor: product.is_in_stock ? 'pointer' : 'not-allowed',
                transition: 'all 0.2s',
                fontFamily: 'inherit',
              }}
            >
              {added ? '✓ Added' : adding ? '...' : !product.is_in_stock ? 'Out of Stock' : 'Add to Cart'}
            </button>
          </div>
        </div>
      </div>
    </Link>
  );
}

export default ProductCard;
