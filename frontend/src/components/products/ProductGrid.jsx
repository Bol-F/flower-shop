import React from 'react';
import { useTranslation } from 'react-i18next';
import ProductCard from './ProductCard';
import LoadingSpinner from '../common/LoadingSpinner';

function ProductGrid({ products, loading }) {
  const { t } = useTranslation();
  if (loading) return <LoadingSpinner message={t('grid.loading')} />;

  if (!products.length) {
    return (
      <div className="empty-state">
        <div style={{ fontSize: '4rem', marginBottom: '16px' }}>🌷</div>
        <h3>{t('grid.noFlowers')}</h3>
        <p>{t('grid.tryAdjusting')}</p>
      </div>
    );
  }

  return (
    <div className="product-grid">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}

export default ProductGrid;
