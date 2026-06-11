import React from 'react';

function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '80px 20px',
      gap: '16px',
    }}>
      <div style={{
        width: '48px',
        height: '48px',
        border: '4px solid #f0e0e6',
        borderTop: '4px solid #e91e8c',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <p style={{ color: '#757575', fontSize: '0.95rem' }}>{message}</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default LoadingSpinner;
