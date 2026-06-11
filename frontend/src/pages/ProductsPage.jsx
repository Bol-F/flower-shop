import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useProducts } from '../hooks/useProducts';
import ProductGrid from '../components/products/ProductGrid';
import ProductFilter from '../components/products/ProductFilter';

function ProductsPage() {
  const [searchParams] = useSearchParams();
  const [filters, setFilters] = useState({
    category: searchParams.get('category') || '',
    search: '',
    min_price: '',
    max_price: '',
    ordering: '-created_at',
  });

  const cleanFilters = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== '')
  );

  const { products, count, loading } = useProducts(cleanFilters);

  return (
    <div className="page-wrapper">
      <div className="container">
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: '2.5rem',
            color: '#2d2d2d',
          }}>
            Our Flowers
          </h1>
          <p style={{ color: '#757575' }}>
            {loading ? 'Loading...' : `${count} arrangements available`}
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: '280px 1fr',
          gap: '32px',
          alignItems: 'start',
        }}>
          {/* Sidebar Filter */}
          <div style={{ position: 'sticky', top: '90px' }}>
            <ProductFilter filters={filters} onChange={setFilters} />
          </div>

          {/* Product Grid */}
          <div>
            <ProductGrid products={products} loading={loading} />
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .products-layout { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}

export default ProductsPage;
