import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getProducts, deleteProduct } from '../api/products';
import { getOrders, updateOrderStatus } from '../api/orders';
import { formatPrice, formatDate } from '../utils/helpers';
import LoadingSpinner from '../components/common/LoadingSpinner';

const TABS = [
  { key: 'Products', labelKey: 'admin.tabProducts' },
  { key: 'Orders', labelKey: 'admin.tabOrders' },
];

function AdminDashboard() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('Products');
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAll = async () => {
      const [prodRes, orderRes] = await Promise.all([
        getProducts({ page_size: 50 }),
        getOrders(),
      ]);
      setProducts(prodRes.data.results || prodRes.data);
      setOrders(orderRes.data.results || orderRes.data);
      setLoading(false);
    };
    loadAll();
  }, []);

  const handleDeleteProduct = async (slug) => {
    if (!window.confirm(t('admin.confirmDelete'))) return;
    await deleteProduct(slug);
    setProducts((prev) => prev.filter((p) => p.slug !== slug));
  };

  const handleStatusChange = async (orderId, newStatus) => {
    await updateOrderStatus(orderId, newStatus);
    setOrders((prev) =>
      prev.map((o) => (o.id === orderId ? { ...o, status: newStatus, status_display: newStatus } : o))
    );
  };

  if (loading) return <LoadingSpinner message={t('admin.loading')} />;

  return (
    <div className="page-wrapper">
      <div className="container">
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: '2.2rem',
          marginBottom: '8px',
        }}>
          {t('admin.title')}
        </h1>
        <p style={{ color: '#757575', marginBottom: '32px' }}>
          {t('admin.subtitle')}
        </p>

        {/* Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '20px',
          marginBottom: '36px',
        }}>
          {[
            { label: t('admin.totalProducts'), value: products.length, icon: '🌸' },
            { label: t('admin.totalOrders'), value: orders.length, icon: '📦' },
            { label: t('admin.pendingOrders'), value: orders.filter((o) => o.status === 'pending').length, icon: '⏳' },
            { label: t('admin.revenue'), value: formatPrice(orders.reduce((sum, o) => sum + parseFloat(o.total_price), 0)), icon: '💰' },
          ].map((stat) => (
            <div key={stat.label} style={{
              background: '#fff',
              borderRadius: '12px',
              padding: '20px',
              boxShadow: '0 2px 8px rgba(233,30,140,0.06)',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>{stat.icon}</div>
              <p style={{ color: '#757575', fontSize: '0.85rem' }}>{stat.label}</p>
              <p style={{ fontWeight: '700', fontSize: '1.4rem', color: '#e91e8c' }}>{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '4px', marginBottom: '24px', background: '#f0e0e6', borderRadius: '10px', padding: '4px', width: 'fit-content' }}>
          {TABS.map((tab) => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{
              padding: '10px 24px',
              borderRadius: '8px',
              border: 'none',
              fontFamily: 'inherit',
              fontWeight: '600',
              cursor: 'pointer',
              background: activeTab === tab.key ? '#e91e8c' : 'transparent',
              color: activeTab === tab.key ? '#fff' : '#e91e8c',
              transition: 'all 0.2s',
            }}>
              {t(tab.labelKey)}
            </button>
          ))}
        </div>

        {/* Products Table */}
        {activeTab === 'Products' && (
          <div style={{ background: '#fff', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 2px 12px rgba(233,30,140,0.06)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ background: '#fff8f9' }}>
                <tr>
                  {[t('admin.thProduct'), t('admin.thCategory'), t('admin.thPrice'), t('admin.thStock'), t('admin.thStatus'), t('admin.thActions')].map((h) => (
                    <th key={h} style={{ padding: '14px 16px', textAlign: 'left', fontSize: '0.85rem', color: '#757575', fontWeight: '600' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id} style={{ borderTop: '1px solid #f0e0e6' }}>
                    <td style={{ padding: '14px 16px', fontWeight: '500' }}>{product.name}</td>
                    <td style={{ padding: '14px 16px', color: '#757575' }}>{product.category_name || '—'}</td>
                    <td style={{ padding: '14px 16px', color: '#e91e8c', fontWeight: '600' }}>{formatPrice(product.price)}</td>
                    <td style={{ padding: '14px 16px' }}>{product.stock ?? '—'}</td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{
                        background: product.is_available ? '#e8f5e9' : '#ffebee',
                        color: product.is_available ? '#2e7d32' : '#c62828',
                        padding: '3px 10px',
                        borderRadius: '12px',
                        fontSize: '0.78rem',
                        fontWeight: '600',
                      }}>
                        {product.is_available ? t('admin.active') : t('admin.hidden')}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <button
                        onClick={() => handleDeleteProduct(product.slug)}
                        style={{
                          color: '#f44336',
                          background: 'none',
                          border: '1px solid #f44336',
                          borderRadius: '6px',
                          padding: '5px 12px',
                          cursor: 'pointer',
                          fontSize: '0.8rem',
                          fontFamily: 'inherit',
                        }}
                      >
                        {t('admin.delete')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Orders Table */}
        {activeTab === 'Orders' && (
          <div style={{ background: '#fff', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 2px 12px rgba(233,30,140,0.06)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ background: '#fff8f9' }}>
                <tr>
                  {[t('admin.thOrder'), t('admin.thCustomer'), t('admin.thTotal'), t('admin.thDate'), t('admin.thStatus'), t('admin.thUpdate')].map((h) => (
                    <th key={h} style={{ padding: '14px 16px', textAlign: 'left', fontSize: '0.85rem', color: '#757575', fontWeight: '600' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id} style={{ borderTop: '1px solid #f0e0e6' }}>
                    <td style={{ padding: '14px 16px', fontWeight: '500' }}>#{order.id}</td>
                    <td style={{ padding: '14px 16px', color: '#757575' }}>{order.shipping_address?.split(',')[0]}</td>
                    <td style={{ padding: '14px 16px', color: '#e91e8c', fontWeight: '600' }}>{formatPrice(order.total_price)}</td>
                    <td style={{ padding: '14px 16px', color: '#757575', fontSize: '0.85rem' }}>{formatDate(order.created_at)}</td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ fontWeight: '500' }}>{order.status_display || order.status}</span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <select
                        value={order.status}
                        onChange={(e) => handleStatusChange(order.id, e.target.value)}
                        style={{
                          border: '1px solid #f0e0e6',
                          borderRadius: '6px',
                          padding: '5px 10px',
                          fontFamily: 'inherit',
                          fontSize: '0.85rem',
                          cursor: 'pointer',
                        }}
                      >
                        {['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'].map((s) => (
                          <option key={s} value={s}>{t(`status.${s}`)}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
