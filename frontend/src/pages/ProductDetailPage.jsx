import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getProduct } from '../api/products';
import { useCart } from '../hooks/useCart';
import { useAuth } from '../hooks/useAuth';
import { formatPrice, getImageUrl } from '../utils/helpers';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Button from '../components/common/Button';

function ProductDetailPage() {
  const { t } = useTranslation();
  const { slug } = useParams();
  const { addItem } = useCart();
  const { isAuthenticated } = useAuth();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    setLoading(true);
    getProduct(slug)
      .then(({ data }) => setProduct(data))
      .finally(() => setLoading(false));
  }, [slug]);

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      window.location.href = '/login';
      return;
    }
    setAdding(true);
    try {
      await addItem(product.id, quantity);
      setMessage({ type: 'success', text: t('product.addedToCart', { name: product.name }) });
    } catch {
      setMessage({ type: 'error', text: t('product.addError') });
    } finally {
      setAdding(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  if (loading) return <LoadingSpinner message={t('product.loading')} />;
  if (!product) return (
    <div className="page-wrapper">
      <div className="container empty-state">
        <div style={{ fontSize: '4rem', marginBottom: '16px' }}>🔍</div>
        <h3>{t('product.notFound')}</h3>
        <Link to="/products" style={{ color: '#e91e8c', fontWeight: '600' }}>{t('product.backToShop')}</Link>
      </div>
    </div>
  );

  return (
    <div className="page-wrapper">
      <div className="container">
        {/* Breadcrumb */}
        <div style={{ marginBottom: '32px', color: '#757575', fontSize: '0.9rem' }}>
          <Link to="/" style={{ color: '#757575' }}>{t('product.home')}</Link>
          {' / '}
          <Link to="/products" style={{ color: '#757575' }}>{t('nav.shop')}</Link>
          {' / '}
          <span style={{ color: '#2d2d2d' }}>{product.name}</span>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '60px',
          alignItems: 'start',
        }}>
          {/* Image */}
          <div style={{
            borderRadius: '20px',
            overflow: 'hidden',
            background: '#fff0f5',
            aspectRatio: '1',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '10rem',
          }}>
            {product.image ? (
              <img
                src={getImageUrl(product.image)}
                alt={product.name}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            ) : '🌸'}
          </div>

          {/* Details */}
          <div>
            {product.category && (
              <Link
                to={`/products?category=${product.category.slug}`}
                style={{ color: '#e91e8c', fontWeight: '600', fontSize: '0.85rem', letterSpacing: '1px' }}
              >
                {product.category.name.toUpperCase()}
              </Link>
            )}
            <h1 style={{
              fontFamily: "'Playfair Display', serif",
              fontSize: '2.2rem',
              margin: '8px 0 16px',
            }}>
              {product.name}
            </h1>

            <p style={{ fontSize: '2rem', fontWeight: '700', color: '#e91e8c', marginBottom: '20px' }}>
              {formatPrice(product.price)}
            </p>

            <p style={{ color: '#4a4a4a', lineHeight: '1.8', marginBottom: '32px' }}>
              {product.description}
            </p>

            {/* Stock Badge */}
            <div style={{ marginBottom: '24px' }}>
              {product.is_in_stock ? (
                <span style={{ background: '#e8f5e9', color: '#2e7d32', padding: '6px 14px', borderRadius: '20px', fontSize: '0.85rem', fontWeight: '600' }}>
                  {t('product.inStock', { count: product.stock })}
                </span>
              ) : (
                <span style={{ background: '#ffebee', color: '#c62828', padding: '6px 14px', borderRadius: '20px', fontSize: '0.85rem', fontWeight: '600' }}>
                  {t('product.outOfStock')}
                </span>
              )}
            </div>

            {/* Quantity + Add to Cart */}
            {product.is_in_stock && (
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  border: '1.5px solid #f0e0e6',
                  borderRadius: '8px',
                  overflow: 'hidden',
                }}>
                  <button onClick={() => setQuantity(Math.max(1, quantity - 1))} style={qtyBtnStyle}>−</button>
                  <span style={{ padding: '0 20px', fontWeight: '600', fontSize: '1.1rem' }}>{quantity}</span>
                  <button onClick={() => setQuantity(Math.min(product.stock, quantity + 1))} style={qtyBtnStyle}>+</button>
                </div>
                <Button onClick={handleAddToCart} loading={adding} style={{ flex: 1 }}>
                  {t('product.addToCart')}
                </Button>
              </div>
            )}

            {/* Feedback Message */}
            {message && (
              <div style={{
                padding: '12px 16px',
                borderRadius: '8px',
                background: message.type === 'success' ? '#e8f5e9' : '#ffebee',
                color: message.type === 'success' ? '#2e7d32' : '#c62828',
                marginBottom: '16px',
              }}>
                {message.text}
              </div>
            )}

            {/* Perks */}
            <div style={{ borderTop: '1px solid #f0e0e6', paddingTop: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {['product.perkDelivery', 'product.perkFresh', 'product.perkGift'].map((perk) => (
                <p key={perk} style={{ color: '#4a4a4a', fontSize: '0.9rem' }}>{t(perk)}</p>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .product-detail-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}

const qtyBtnStyle = {
  padding: '10px 16px',
  background: 'none',
  border: 'none',
  cursor: 'pointer',
  fontSize: '1.2rem',
  color: '#e91e8c',
  fontWeight: '600',
};

export default ProductDetailPage;
