import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { updateProfile } from '../api/auth';
import { extractErrorMessage } from '../utils/helpers';
import Button from '../components/common/Button';
import ErrorMessage from '../components/common/ErrorMessage';

function ProfilePage() {
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
          My Profile
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
                  Admin
                </span>
              )}
            </div>
          </div>

          {success && (
            <div style={{ background: '#e8f5e9', color: '#2e7d32', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px' }}>
              ✓ Profile updated successfully!
            </div>
          )}
          {error && <ErrorMessage message={error} />}

          {editing ? (
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Username</label>
                <input name="username" value={form.username} onChange={handleChange} className="form-control" />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input name="phone" type="tel" value={form.phone} onChange={handleChange} className="form-control" placeholder="+1 (555) 123-4567" />
              </div>
              <div className="form-group">
                <label>Address</label>
                <textarea name="address" value={form.address} onChange={handleChange} className="form-control" rows={3} placeholder="Your delivery address" />
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <Button type="submit" loading={saving}>Save Changes</Button>
                <Button variant="secondary" onClick={() => setEditing(false)}>Cancel</Button>
              </div>
            </form>
          ) : (
            <div>
              <InfoRow label="Email" value={user?.email} />
              <InfoRow label="Phone" value={user?.phone || 'Not set'} />
              <InfoRow label="Address" value={user?.address || 'Not set'} />
              <InfoRow label="Member since" value={new Date(user?.date_joined).toLocaleDateString()} />
              <Button onClick={() => setEditing(true)} style={{ marginTop: '16px' }}>
                Edit Profile
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
