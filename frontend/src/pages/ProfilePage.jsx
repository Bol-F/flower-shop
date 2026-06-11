import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import { updateProfile } from '../api/auth';
import { extractErrorMessage } from '../utils/helpers';
import Button from '../components/common/Button';
import ErrorMessage from '../components/common/ErrorMessage';

function ProfilePage() {
  const { t } = useTranslation();
  const { user, refreshUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const [form, setForm] = useState({
    username: user?.username || '',
    phone: user?.phone || '',
    address: user?.address || '',
  });

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await updateProfile(form);
      await refreshUser();
      setEditing(false);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-wrapper">
      <div className="container" style={{ maxWidth: '600px' }}>
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: '2.2rem',
          marginBottom: '32px',
        }}>
          {t('profile.title')}
        </h1>

        <div style={{
          background: '#fff',
          borderRadius: '16px',
          padding: '32px',
          boxShadow: '0 2px 12px rgba(233,30,140,0.06)',
        }}>
          {/* Avatar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '32px' }}>
            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '2rem',
              color: '#fff',
              fontWeight: '700',
            }}>
              {user?.username?.[0]?.toUpperCase() || '?'}
            </div>
            <div>
              <h2 style={{ fontFamily: "'Playfair Display', serif" }}>{user?.username}</h2>
              <p style={{ color: '#757575' }}>{user?.email}</p>
              {user?.is_staff && (
                <span style={{ background: '#e8f5e9', color: '#2e7d32', padding: '3px 10px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: '600' }}>
                  {t('profile.admin')}
                </span>
              )}
            </div>
          </div>

          {success && (
            <div style={{ background: '#e8f5e9', color: '#2e7d32', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px' }}>
              {t('profile.updated')}
            </div>
          )}
          {error && <ErrorMessage message={error} />}

          {editing ? (
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>{t('profile.username')}</label>
                <input name="username" value={form.username} onChange={handleChange} className="form-control" />
              </div>
              <div className="form-group">
                <label>{t('profile.phone')}</label>
                <input name="phone" type="tel" value={form.phone} onChange={handleChange} className="form-control" placeholder="+1 (555) 123-4567" />
              </div>
              <div className="form-group">
                <label>{t('profile.address')}</label>
                <textarea name="address" value={form.address} onChange={handleChange} className="form-control" rows={3} placeholder={t('profile.addressPlaceholder')} />
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <Button type="submit" loading={saving}>{t('profile.save')}</Button>
                <Button variant="secondary" onClick={() => setEditing(false)}>{t('profile.cancel')}</Button>
              </div>
            </form>
          ) : (
            <div>
              <InfoRow label={t('profile.email')} value={user?.email} />
              <InfoRow label={t('profile.phone')} value={user?.phone || t('profile.notSet')} />
              <InfoRow label={t('profile.address')} value={user?.address || t('profile.notSet')} />
              <InfoRow label={t('profile.memberSince')} value={new Date(user?.date_joined).toLocaleDateString()} />
              <Button onClick={() => setEditing(true)} style={{ marginTop: '16px' }}>
                {t('profile.edit')}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      padding: '12px 0',
      borderBottom: '1px solid #f0e0e6',
    }}>
      <span style={{ color: '#757575', fontWeight: '500' }}>{label}</span>
      <span style={{ color: '#2d2d2d' }}>{value}</span>
    </div>
  );
}

export default ProfilePage;
