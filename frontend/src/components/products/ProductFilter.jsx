import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getCategories } from '../../api/categories';

function ProductFilter({ filters, onChange }) {
  const { t } = useTranslation();
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
        {t('filter.title')}
      </h3>

      {/* Search */}
      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>{t('filter.search')}</label>
        <input
          type="text"
          placeholder={t('filter.searchPlaceholder')}
          value={filters.search || ''}
          onChange={(e) => handleChange('search', e.target.value)}
          style={inputStyle}
        />
      </div>

      {/* Category */}
      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>{t('filter.category')}</label>
        <select
          value={filters.category || ''}
          onChange={(e) => handleChange('category', e.target.value)}
          style={inputStyle}
        >
          <option value="">{t('filter.allCategories')}</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.slug}>{cat.name}</option>
          ))}
        </select>
      </div>

      {/* Price Range */}
      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>{t('filter.minPrice')}</label>
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
        <label style={labelStyle}>{t('filter.maxPrice')}</label>
        <input
          type="number"
          placeholder={t('filter.any')}
          value={filters.max_price || ''}
          onChange={(e) => handleChange('max_price', e.target.value)}
          style={inputStyle}
          min="0"
        />
      </div>

      {/* Sort */}
      <div style={{ marginBottom: '20px' }}>
        <label style={labelStyle}>{t('filter.sortBy')}</label>
        <select
          value={filters.ordering || ''}
          onChange={(e) => handleChange('ordering', e.target.value)}
          style={inputStyle}
        >
          <option value="-created_at">{t('filter.newestFirst')}</option>
          <option value="price">{t('filter.priceLowHigh')}</option>
          <option value="-price">{t('filter.priceHighLow')}</option>
          <option value="name">{t('filter.nameAZ')}</option>
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
        {t('filter.clear')}
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
