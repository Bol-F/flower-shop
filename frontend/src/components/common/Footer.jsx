import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

function Footer() {
  const { t } = useTranslation();
  return (
    <footer style={{
      background: '#2d2d2d',
      color: '#ccc',
      padding: '60px 0 30px',
      marginTop: 'auto',
    }}>
      <div className="container">
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '40px',
          marginBottom: '40px',
        }}>
          <div>
            <h3 style={{
              fontFamily: "'Playfair Display', serif",
              color: '#e91e8c',
              fontSize: '1.4rem',
              marginBottom: '16px',
            }}>
              🌸 Bloom & Petal
            </h3>
            <p style={{ fontSize: '0.9rem', lineHeight: '1.7' }}>
              {t('footer.tagline')}
            </p>
          </div>

          <div>
            <h4 style={{ color: '#fff', marginBottom: '16px' }}>{t('footer.shop')}</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link to="/products" style={linkStyle}>{t('footer.allFlowers')}</Link>
              <Link to="/products?category=roses" style={linkStyle}>{t('footer.roses')}</Link>
              <Link to="/products?category=bouquets" style={linkStyle}>{t('footer.bouquets')}</Link>
            </div>
          </div>

          <div>
            <h4 style={{ color: '#fff', marginBottom: '16px' }}>{t('footer.account')}</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link to="/login" style={linkStyle}>{t('footer.login')}</Link>
              <Link to="/register" style={linkStyle}>{t('footer.register')}</Link>
              <Link to="/orders" style={linkStyle}>{t('footer.myOrders')}</Link>
            </div>
          </div>

          <div>
            <h4 style={{ color: '#fff', marginBottom: '16px' }}>{t('footer.contact')}</h4>
            <p style={{ fontSize: '0.9rem', lineHeight: '1.7' }}>
              📍 123 Flower Street<br />
              📞 +1 (555) 123-4567<br />
              ✉️ hello@bloomandpetal.com
            </p>
          </div>
        </div>

        <div style={{
          borderTop: '1px solid #444',
          paddingTop: '24px',
          textAlign: 'center',
          fontSize: '0.85rem',
        }}>
          © {new Date().getFullYear()} Bloom & Petal. {t('footer.rights')}
        </div>
      </div>
    </footer>
  );
}

const linkStyle = {
  color: '#ccc',
  fontSize: '0.9rem',
  transition: 'color 0.2s',
};

export default Footer;
