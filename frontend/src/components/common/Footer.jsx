import React from 'react';
import { Link } from 'react-router-dom';

function Footer() {
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
              Fresh flowers delivered to your door. Spreading joy one bouquet at a time.
            </p>
          </div>

          <div>
            <h4 style={{ color: '#fff', marginBottom: '16px' }}>Shop</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link to="/products" style={linkStyle}>All Flowers</Link>
              <Link to="/products?category=roses" style={linkStyle}>Roses</Link>
              <Link to="/products?category=bouquets" style={linkStyle}>Bouquets</Link>
            </div>
          </div>

          <div>
            <h4 style={{ color: '#fff', marginBottom: '16px' }}>Account</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link to="/login" style={linkStyle}>Login</Link>
              <Link to="/register" style={linkStyle}>Register</Link>
              <Link to="/orders" style={linkStyle}>My Orders</Link>
            </div>
          </div>

          <div>
            <h4 style={{ color: '#fff', marginBottom: '16px' }}>Contact</h4>
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
          © {new Date().getFullYear()} Bloom & Petal. All rights reserved.
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
