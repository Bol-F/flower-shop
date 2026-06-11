import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getOrders } from '../api/orders';
import { formatPrice, formatDate, getStatusColor } from '../utils/helpers';
import LoadingSpinner from '../components/common/LoadingSpinner';

function OrderHistoryPage() {
  const { t } = useTranslation();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  const justOrdered = location.state?.success;

  useEffect(() => {
    getOrders()
      .then(({ data }) => setOrders(data.results || data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message={t('orders.loading')} />;

  return (
    <div className="page-wrapper">
      <div className="container">
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: '2.2rem',
          marginBottom: '32px',
        }}>
          {t('orders.title')}
        </h1>

        {justOrdered && (
          <div style={{
            background: '#e8f5e9',
            color: '#2e7d32',
            padding: '16px 20px',
            borderRadius: '12px',
            marginBottom: '24px',
            fontSize: '1rem',
          }}>
            {t('orders.placedSuccess')}
          </div>
        )}

        {orders.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: '4rem', marginBottom: '16px' }}>📦</div>
            <h3>{t('orders.noOrders')}</h3>
            <p style={{ marginBottom: '24px' }}>{t('orders.willAppear')}</p>
            <Link to="/products" style={{
              background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
              color: '#fff',
              padding: '12px 28px',
              borderRadius: '8px',
              fontWeight: '600',
            }}>
              {t('orders.startShopping')}
            </Link>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {orders.map((order) => (
              <OrderCard key={order.id} order={order} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function OrderCard({ order }) {
  const { t } = useTranslation();
  const statusColor = getStatusColor(order.status);
  const badgeColors = {
    success: { bg: '#e8f5e9', text: '#2e7d32' },
    error: { bg: '#ffebee', text: '#c62828' },
    warning: { bg: '#fff3e0', text: '#e65100' },
    info: { bg: '#e3f2fd', text: '#1565c0' },
  };
  const badge = badgeColors[statusColor] || badgeColors.info;

  return (
    <Link to={`/orders/${order.id}`} style={{ textDecoration: 'none' }}>
      <div style={{
        background: '#fff',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 2px 12px rgba(233,30,140,0.06)',
        transition: 'box-shadow 0.2s',
        cursor: 'pointer',
      }}
        onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 20px rgba(233,30,140,0.12)'}
        onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 2px 12px rgba(233,30,140,0.06)'}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <p style={{ color: '#757575', fontSize: '0.85rem', marginBottom: '4px' }}>
              {t('orders.orderMeta', { id: order.id, date: formatDate(order.created_at) })}
            </p>
            <p style={{ fontWeight: '600', fontSize: '1.1rem' }}>
              {t('common.itemCount', { count: order.items?.length || 0 })}
            </p>
            <p style={{ color: '#757575', fontSize: '0.9rem', marginTop: '4px' }}>
              {order.shipping_address}
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{
              background: badge.bg,
              color: badge.text,
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '0.8rem',
              fontWeight: '600',
              display: 'block',
              marginBottom: '8px',
            }}>
              {order.status_display}
            </span>
            <p style={{ fontWeight: '700', color: '#e91e8c', fontSize: '1.15rem' }}>
              {formatPrice(order.total_price)}
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}

export default OrderHistoryPage;
