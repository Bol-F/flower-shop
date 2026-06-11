import React, { useState, useEffect } from 'react';
import { getCategories } from '../../api/categories';

function ProductFilter({ filters, onChange }) {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    getCategories().then(({ data }) => {
      setCategories(data.results || data);
    });
  }, []);

  const handleChange = (key, value) => {
    onChange({ ...filters, [key]: value });
  };

  const inputStyle = {
    padding: '10px 14px',
    border: '1.5px solid #f0e0e6',
    borderRadius: '8px',
    fontSize: '0.9rem',
    background: '#fff',
    outline: 'none',
    width: '100%',
    fontFamily: 'inherit',
  };

  return (
    <div style={{
      background: '#fff',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 2px 12px rgba(233,30,140,0.06)',
    }}>
      <h3 style={{
        fontFamily: "'Playfair Display', serif",
        marginBottom: '20px',
        color: '#2d2d2d',
      }}>
        Filter
      </h3>

      {/* Search */}
      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>Search</label>
        <input
          type="text"
          placeholder="Search flowers..."
          value={filters.search || ''}
          onChange={(e) => handleChange('search', e.target.value)}
          style={inputStyle}
        />
      </div>

      {/* Category */}
      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>Category</label>
        <select
          value={filters.category || ''}
          onChange={(e) => handleChange('category', e.target.value)}
          style={inputStyle}
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.slug}>{cat.name}</option>
          ))}
        </select>
      </div>

      {/* Price Range */}
      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>Min Price ($)</label>
        <input
          type="number"
          placeholder="0"
          value={filters.min_price || ''}
          onChange={(e) => handleChange('min_price', e.target.value)}
          style={inputStyle}
          min="0"
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>Max Price ($)</label>
        <input
          type="number"
          placeholder="Any"
          value={filters.max_price || ''}
          onChange={(e) => handleChange('max_price', e.target.value)}
          style={inputStyle}
          min="0"
        />
      </div>

      {/* Sort */}
      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>Sort By</label>
        <select
          value={filters.ordering || ''}
          onChange={(e) => handleChange('ordering', e.target.value)}
          style={inputStyle}
        >
          <option value="-created_at">Newest First</option>
          <option value="price">Price: Low to High</option>
          <option value="-price">Price: High to Low</option>
          <option value="name">Name A-Z</option>
        </select>
      </div>

      {/* Clear Filters */}
      <button
        onClick={() => onChange({})}
        style={{
          width: '100%',
          padding: '10px',
          border: '1.5px solid #e91e8c',
          borderRadius: '8px',
          color: '#e91e8c',
          background: 'transparent',
          fontWeight: '600',
          cursor: 'pointer',
          fontFamily: 'inherit',
        }}
      >
        Clear Filters
      </button>
    </div>
  );
}

const labelStyle = {
  display: 'block',
  fontSize: '0.85rem',
  fontWeight: '600',
  color: '#4a4a4a',
  marginBottom: '8px',
};

export default ProductFilter;
