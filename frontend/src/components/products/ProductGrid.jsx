import React from 'react';
import ProductCard from './ProductCard';
import LoadingSpinner from '../common/LoadingSpinner';

function ProductGrid({ products, loading }) {
  if (loading) return <LoadingSpinner message="Loading flowers..." />;

  if (!products.length) {
    return (
      <div className="empty-state">
        <div style={{ fontSize: '4rem', marginBottom: '16px' }}>🌷</div>
        <h3>No flowers found</h3>
        <p>Try adjusting your filters or search term.</p>
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
