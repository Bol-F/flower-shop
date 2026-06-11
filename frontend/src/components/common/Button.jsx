import React from 'react';

const styles = {
  base: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '12px 24px',
    borderRadius: '8px',
    fontWeight: '600',
    fontSize: '0.95rem',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    border: 'none',
    fontFamily: 'inherit',
  },
  primary: {
    background: 'linear-gradient(135deg, #e91e8c, #c2185b)',
    color: '#fff',
  },
  secondary: {
    background: 'transparent',
    color: '#e91e8c',
    border: '2px solid #e91e8c',
  },
  ghost: {
    background: 'transparent',
    color: '#4a4a4a',
  },
  danger: {
    background: '#f44336',
    color: '#fff',
  },
  small: { padding: '8px 16px', fontSize: '0.85rem' },
  large: { padding: '16px 32px', fontSize: '1.05rem' },
  fullWidth: { width: '100%' },
  disabled: { opacity: 0.6, cursor: 'not-allowed' },
};

function Button({
  children,
  variant = 'primary',
  size,
  fullWidth = false,
  disabled = false,
  loading = false,
  onClick,
  type = 'button',
  style = {},
}) {
  const combinedStyle = {
    ...styles.base,
    ...styles[variant],
    ...(size && styles[size]),
    ...(fullWidth && styles.fullWidth),
    ...(disabled || loading ? styles.disabled : {}),
    ...style,
  };

  return (
    <button
      type={type}
      style={combinedStyle}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading && <span>⏳</span>}
      {children}
    </button>
  );
}

export default Button;
