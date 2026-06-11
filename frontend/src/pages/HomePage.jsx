import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getProducts } from '../api/products';
import { getCategories } from '../api/categories';
import ProductGrid from '../components/products/ProductGrid';

function HomePage() {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getProducts({ ordering: '-created_at', page_size: 8 }),
      getCategories(),
    ]).then(([productsRes, categoriesRes]) => {
      setFeaturedProducts(productsRes.data.results || productsRes.data);
      setCategories((categoriesRes.data.results || categoriesRes.data).slice(0, 4));
    }).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      {/* Hero Section */}
      <section style={{
        background: 'linear-gradient(135deg, #fff0f7 0%, #ffe8f3 50%, #fff8f9 100%)',
        padding: '80px 0',
        textAlign: 'center',
      }}>
        <div className="container">
          <p style={{ color: '#e91e8c', fontWeight: '600', letterSpacing: '2px', fontSize: '0.85rem', marginBottom: '16px' }}>
            FRESH DAILY • HANDCRAFTED • DELIVERED WITH LOVE
          </p>
          <h1 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
            color: '#2d2d2d',
            marginBottom: '24px',
            lineHeight: '1.1',
          }}>
            Beautiful Flowers<br />
            <span style={{ color: '#e91e8c' }}>For Every Moment</span>
          </h1>
          <p style={{ fontSize: '1.1rem', color: '#757575', marginBottom: '40px', maxWidth: '500px', margin: '0 auto 40px' }}>
            From romantic roses to cheerful sunflowers — we deliver fresh bouquets straight to your door.
          </p>
          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/products" style={{
              background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
              color: '#fff',
              padding: '16px 36px',
              borderRadius: '30px',
              fontWeight: '700',
              fontSize: '1rem',
              boxShadow: '0 4px 20px rgba(233,30,140,0.3)',
            }}>
              Shop Now
            </Link>
            <Link to="/products" style={{
              background: '#fff',
              color: '#e91e8c',
              padding: '16px 36px',
              borderRadius: '30px',
              fontWeight: '700',
              fontSize: '1rem',
              border: '2px solid #e91e8c',
            }}>
              View Collections
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ background: '#fff', padding: '60px 0' }}>
        <div className="container">
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '32px',
            textAlign: 'center',
          }}>
            {[
              { icon: '🌹', title: 'Fresh Flowers', desc: 'Hand-selected daily from local growers' },
              { icon: '🚚', title: 'Same Day Delivery', desc: 'Order by 2pm for same-day arrival' },
              { icon: '💐', title: 'Custom Bouquets', desc: 'Tell us your vision, we make it happen' },
              { icon: '♻️', title: 'Eco Friendly', desc: 'Sustainable packaging, zero waste' },
            ].map((feat) => (
              <div key={feat.title} style={{ padding: '20px' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>{feat.icon}</div>
                <h3 style={{ fontFamily: "'Playfair Display', serif", marginBottom: '8px' }}>{feat.title}</h3>
                <p style={{ color: '#757575', fontSize: '0.9rem' }}>{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      {categories.length > 0 && (
        <section style={{ padding: '60px 0' }}>
          <div className="container">
            <h2 className="section-title" style={{ textAlign: 'center' }}>Shop by Category</h2>
            <p className="section-subtitle" style={{ textAlign: 'center' }}>Find the perfect flowers for any occasion</p>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '20px',
            }}>
              {categories.map((cat) => (
                <Link key={cat.id} to={`/products?category=${cat.slug}`} style={{
                  background: '#fff',
                  borderRadius: '16px',
                  padding: '30px 20px',
                  textAlign: 'center',
                  boxShadow: '0 2px 12px rgba(233,30,140,0.06)',
                  transition: 'transform 0.2s',
                  color: '#2d2d2d',
                }}
                  onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
                  onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                >
                  <div style={{ fontSize: '3rem', marginBottom: '12px' }}>🌷</div>
                  <h3 style={{ fontFamily: "'Playfair Display', serif", marginBottom: '4px' }}>{cat.name}</h3>
                  <p style={{ color: '#e91e8c', fontSize: '0.85rem' }}>{cat.product_count} items</p>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Featured Products */}
      <section style={{ background: '#fff', padding: '60px 0' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h2 className="section-title">Featured Bouquets</h2>
            <Link to="/products" style={{ color: '#e91e8c', fontWeight: '600' }}>View All →</Link>
          </div>
          <p className="section-subtitle">Our most loved arrangements, freshly made</p>
          <ProductGrid products={featuredProducts} loading={loading} />
        </div>
      </section>

      {/* CTA Banner */}
      <section style={{
        background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
        padding: '80px 0',
        textAlign: 'center',
        color: '#fff',
      }}>
        <div className="container">
          <h2 style={{ fontFamily: "'Playfair Display', serif", fontSize: '2.2rem', marginBottom: '16px' }}>
            Ready to Brighten Someone's Day?
          </h2>
          <p style={{ marginBottom: '32px', opacity: 0.9, fontSize: '1.05rem' }}>
            Free delivery on orders over $50
          </p>
          <Link to="/products" style={{
            background: '#fff',
            color: '#e91e8c',
            padding: '16px 40px',
            borderRadius: '30px',
            fontWeight: '700',
            fontSize: '1rem',
          }}>
            Order Now
          </Link>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
