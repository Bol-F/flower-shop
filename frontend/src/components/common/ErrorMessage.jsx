import React from 'react';

function ErrorMessage({ message, onRetry }) {
  return (
    <div style={{
      background: '#ffebee',
      border: '1px solid #ffcdd2',
      borderRadius: '8px',
      padding: '16px 20px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      color: '#c62828',
    }}>
      <span style={{ fontSize: '1.2rem' }}>⚠️</span>
      <span style={{ flex: 1 }}>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            background: '#c62828',
            color: '#fff',
            border: 'none',
            padding: '6px 14px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontFamily: 'inherit',
            fontSize: '0.85rem',
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}

export default ErrorMessage;
