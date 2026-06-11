import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { register } from '../api/auth';
import { extractErrorMessage } from '../utils/helpers';
import Button from '../components/common/Button';
import ErrorMessage from '../components/common/ErrorMessage';

function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    phone: '',
    address: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (form.password !== form.password_confirm) {
      setError(t('register.passwordMismatch'));
      return;
    }

    setLoading(true);
    try {
      await register(form);
      navigate('/login', { state: { message: t('register.accountCreated') } });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #fff0f7 0%, #fff8f9 100%)',
      padding: '40px 20px',
    }}>
      <div style={{
        background: '#fff',
        borderRadius: '20px',
        padding: '48px 40px',
        width: '100%',
        maxWidth: '480px',
        boxShadow: '0 8px 40px rgba(233,30,140,0.12)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '36px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '12px' }}>🌺</div>
          <h1 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: '1.8rem',
            marginBottom: '8px',
          }}>
            {t('register.title')}
          </h1>
          <p style={{ color: '#757575' }}>{t('register.subtitle')}</p>
        </div>

        {error && <ErrorMessage message={error} />}

        <form onSubmit={handleSubmit} style={{ marginTop: error ? '20px' : 0 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
            <div className="form-group">
              <label htmlFor="username">{t('register.username')}</label>
              <input
                id="username"
                name="username"
                value={form.username}
                onChange={handleChange}
                required
                placeholder={t('register.usernamePlaceholder')}
                className="form-control"
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">{t('register.email')}</label>
              <input
                id="email"
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                required
                placeholder="you@example.com"
                className="form-control"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">{t('register.password')}</label>
            <input
              id="password"
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              placeholder={t('register.passwordPlaceholder')}
              className="form-control"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password_confirm">{t('register.confirmPassword')}</label>
            <input
              id="password_confirm"
              type="password"
              name="password_confirm"
              value={form.password_confirm}
              onChange={handleChange}
              required
              placeholder={t('register.confirmPlaceholder')}
              className="form-control"
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">{t('register.phone')}</label>
            <input
              id="phone"
              type="tel"
              name="phone"
              value={form.phone}
              onChange={handleChange}
              placeholder="+1 (555) 123-4567"
              className="form-control"
            />
          </div>

          <Button type="submit" fullWidth loading={loading} size="large" style={{ marginTop: '8px' }}>
            {t('register.submit')}
          </Button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '24px', color: '#757575' }}>
          {t('register.haveAccount')}{' '}
          <Link to="/login" style={{ color: '#e91e8c', fontWeight: '600' }}>
            {t('register.signIn')}
          </Link>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;
