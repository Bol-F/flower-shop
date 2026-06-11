import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { createOrder } from '../api/orders';
import { useCart } from '../hooks/useCart';
import { useAuth } from '../hooks/useAuth';
import { formatPrice, extractErrorMessage } from '../utils/helpers';
import Button from '../components/common/Button';
import ErrorMessage from '../components/common/ErrorMessage';

function CheckoutPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { cart, refreshCart } = useCart();
  const { user } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    shipping_address: user?.address || '',
    phone: user?.phone || '',
    notes: '',
  });

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { data } = await createOrder(form);
      await refreshCart();
      navigate(`/orders/${data.id}`, { state: { success: true } });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const items = cart?.items || [];
  const shipping = parseFloat(cart?.total_price || 0) > 50 ? 0 : 5.99;
  const total = parseFloat(cart?.total_price || 0) + shipping;

  return (
    <div className="page-wrapper">
      <div className="container">
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: '2.2rem',
          marginBottom: '32px',
        }}>
          {t('checkout.title')}
        </h1>

        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 380px',
          gap: '40px',
          alignItems: 'start',
        }}>
          {/* Checkout Form */}
          <div style={{
            background: '#fff',
            borderRadius: '16px',
            padding: '32px',
            boxShadow: '0 2px 12px rgba(233,30,140,0.06)',
          }}>
            <h2 style={{ fontFamily: "'Playfair Display', serif", marginBottom: '24px' }}>
              {t('checkout.deliveryDetails')}
            </h2>

            {error && <ErrorMessage message={error} />}

            <form onSubmit={handleSubmit} style={{ marginTop: '20px' }}>
              <div className="form-group">
                <label htmlFor="shipping_address">{t('checkout.address')}</label>
                <textarea
                  id="shipping_address"
                  name="shipping_address"
                  value={form.shipping_address}
                  onChange={handleChange}
                  required
                  rows={3}
                  placeholder={t('checkout.addressPlaceholder')}
                  className="form-control"
                />
              </div>

              <div className="form-group">
                <label htmlFor="phone">{t('checkout.phone')}</label>
                <input
                  id="phone"
                  type="tel"
                  name="phone"
                  value={form.phone}
                  onChange={handleChange}
                  required
                  placeholder="+1 (555) 123-4567"
                  className="form-control"
                />
              </div>

              <div className="form-group">
                <label htmlFor="notes">{t('checkout.notes')}</label>
                <textarea
                  id="notes"
                  name="notes"
                  value={form.notes}
                  onChange={handleChange}
                  rows={2}
                  placeholder={t('checkout.notesPlaceholder')}
                  className="form-control"
                />
              </div>

              <Button type="submit" fullWidth loading={submitting} size="large">
                {t('checkout.placeOrder', { total: formatPrice(total) })}
              </Button>
            </form>
          </div>

          {/* Order Summary */}
          <div style={{
            background: '#fff',
            borderRadius: '16px',
            padding: '24px',
            boxShadow: '0 2px 12px rgba(233,30,140,0.06)',
            position: 'sticky',
            top: '90px',
          }}>
            <h2 style={{ fontFamily: "'Playfair Display', serif", marginBottom: '20px' }}>
              {t('checkout.yourOrder')}
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
              {items.map((item) => (
                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <span>{item.product.name} × {item.quantity}</span>
                  <span style={{ fontWeight: '600' }}>{formatPrice(item.subtotal)}</span>
                </div>
              ))}
            </div>

            <div style={{ borderTop: '1px solid #f0e0e6', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                <span>{t('checkout.subtotal')}</span>
                <span>{formatPrice(cart?.total_price || 0)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                <span>{t('checkout.shipping')}</span>
                <span style={{ color: shipping === 0 ? '#4caf50' : '#2d2d2d' }}>
                  {shipping === 0 ? t('checkout.free') : formatPrice(shipping)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', fontSize: '1.1rem', marginTop: '8px' }}>
                <span>{t('checkout.total')}</span>
                <span style={{ color: '#e91e8c' }}>{formatPrice(total)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CheckoutPage;
