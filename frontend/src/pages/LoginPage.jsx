import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import { extractErrorMessage } from '../utils/helpers';
import Button from '../components/common/Button';
import ErrorMessage from '../components/common/ErrorMessage';

function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const from = location.state?.from?.pathname || '/';

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(form.email, form.password);
      navigate(from, { replace: true });
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
      padding: '20px',
    }}>
      <div style={{
        background: '#fff',
        borderRadius: '20px',
        padding: '48px 40px',
        width: '100%',
        maxWidth: '440px',
        boxShadow: '0 8px 40px rgba(233,30,140,0.12)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '36px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '12px' }}>🌸</div>
          <h1 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: '1.8rem',
            marginBottom: '8px',
          }}>
            {t('login.welcome')}
          </h1>
          <p style={{ color: '#757575' }}>{t('login.subtitle')}</p>
        </div>

        {error && <ErrorMessage message={error} />}

        <form onSubmit={handleSubmit} style={{ marginTop: error ? '20px' : 0 }}>
          <div className="form-group">
            <label htmlFor="email">{t('login.email')}</label>
            <input
              id="email"
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
              placeholder="you@example.com"
              className="form-control"
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">{t('login.password')}</label>
            <input
              id="password"
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              placeholder="••••••••"
              className="form-control"
              autoComplete="current-password"
            />
          </div>

          <Button type="submit" fullWidth loading={loading} size="large" style={{ marginTop: '8px' }}>
            {t('login.signIn')}
          </Button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '24px', color: '#757575' }}>
          {t('login.noAccount')}{' '}
          <Link to="/register" style={{ color: '#e91e8c', fontWeight: '600' }}>
            {t('login.signUp')}
          </Link>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;
