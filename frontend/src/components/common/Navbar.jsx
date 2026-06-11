import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { useCart } from '../../hooks/useCart';

const LANGUAGES = [
  { code: 'en', label: 'EN' },
  { code: 'ru', label: 'РУ' },
  { code: 'uz', label: "O'Z" },
];

function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const current = (i18n.resolvedLanguage || i18n.language || 'en').slice(0, 2);

  return (
    <div style={{
      display: 'flex',
      gap: '2px',
      background: '#fff0f5',
      borderRadius: '20px',
      padding: '3px',
    }}>
      {LANGUAGES.map((lang) => (
        <button
          key={lang.code}
          onClick={() => i18n.changeLanguage(lang.code)}
          style={{
            border: 'none',
            borderRadius: '16px',
            padding: '5px 10px',
            fontSize: '0.75rem',
            fontWeight: '700',
            cursor: 'pointer',
            fontFamily: 'inherit',
            background: current === lang.code ? '#e91e8c' : 'transparent',
            color: current === lang.code ? '#fff' : '#e91e8c',
            transition: 'all 0.2s',
          }}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}

function Navbar() {
  const { t } = useTranslation();
  const { isAuthenticated, isAdmin, logout } = useAuth();
  const { totalItems } = useCart();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
    setMenuOpen(false);
  };

  return (
    <nav style={{
      background: '#fff',
      boxShadow: '0 2px 12px rgba(233,30,140,0.08)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div className="container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '72px',
      }}>
        {/* Logo */}
        <Link to="/" style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: '1.5rem',
          fontWeight: '700',
          color: '#e91e8c',
        }}>
          🌸 Bloom & Petal
        </Link>

        {/* Desktop Navigation */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '32px',
        }} className="desktop-nav">
          <Link to="/products" style={navLinkStyle}>{t('nav.shop')}</Link>

          {isAuthenticated ? (
            <>
              <Link to="/orders" style={navLinkStyle}>{t('nav.myOrders')}</Link>
              <Link to="/profile" style={navLinkStyle}>{t('nav.profile')}</Link>
              {isAdmin && (
                <Link to="/admin" style={{ ...navLinkStyle, color: '#e91e8c' }}>
                  {t('nav.admin')}
                </Link>
              )}
              <button onClick={handleLogout} style={navLinkStyle}>{t('nav.logout')}</button>
            </>
          ) : (
            <>
              <Link to="/login" style={navLinkStyle}>{t('nav.login')}</Link>
              <Link to="/register" style={{
                background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
                color: '#fff',
                padding: '8px 20px',
                borderRadius: '20px',
                fontWeight: '600',
                fontSize: '0.9rem',
              }}>
                {t('nav.signUp')}
              </Link>
            </>
          )}

          <LanguageSwitcher />

          <Link to="/cart" style={{ position: 'relative', fontSize: '1.4rem' }}>
            🛒
            {totalItems > 0 && (
              <span style={{
                position: 'absolute',
                top: '-8px',
                right: '-10px',
                background: '#e91e8c',
                color: '#fff',
                borderRadius: '50%',
                width: '20px',
                height: '20px',
                fontSize: '0.7rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '700',
              }}>
                {totalItems}
              </span>
            )}
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          style={{ display: 'none', fontSize: '1.5rem', background: 'none', border: 'none', cursor: 'pointer' }}
          className="mobile-menu-btn"
        >
          {menuOpen ? '✕' : '☰'}
        </button>
      </div>

      {/* Mobile Dropdown */}
      {menuOpen && (
        <div style={{
          background: '#fff',
          borderTop: '1px solid #f0e0e6',
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}>
          <Link to="/products" onClick={() => setMenuOpen(false)} style={navLinkStyle}>{t('nav.shop')}</Link>
          <Link to="/cart" onClick={() => setMenuOpen(false)} style={navLinkStyle}>{t('nav.cart')} ({totalItems})</Link>
          {isAuthenticated ? (
            <>
              <Link to="/orders" onClick={() => setMenuOpen(false)} style={navLinkStyle}>{t('nav.myOrders')}</Link>
              <Link to="/profile" onClick={() => setMenuOpen(false)} style={navLinkStyle}>{t('nav.profile')}</Link>
              {isAdmin && (
                <Link to="/admin" onClick={() => setMenuOpen(false)} style={navLinkStyle}>{t('nav.admin')}</Link>
              )}
              <button onClick={handleLogout} style={navLinkStyle}>{t('nav.logout')}</button>
            </>
          ) : (
            <>
              <Link to="/login" onClick={() => setMenuOpen(false)} style={navLinkStyle}>{t('nav.login')}</Link>
              <Link to="/register" onClick={() => setMenuOpen(false)} style={navLinkStyle}>{t('nav.register')}</Link>
            </>
          )}
          <LanguageSwitcher />
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .desktop-nav { display: none !important; }
          .mobile-menu-btn { display: block !important; }
        }
      `}</style>
    </nav>
  );
}

const navLinkStyle = {
  color: '#4a4a4a',
  fontWeight: '500',
  fontSize: '0.95rem',
  cursor: 'pointer',
  background: 'none',
  border: 'none',
  fontFamily: 'inherit',
  transition: 'color 0.2s',
};

export default Navbar;
