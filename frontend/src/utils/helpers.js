import i18n from '../i18n';

export const formatPrice = (price) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price);

export const formatDate = (dateString) =>
  new Date(dateString).toLocaleDateString(i18n.language || 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

export const getImageUrl = (imagePath) => {
  if (!imagePath) return '/placeholder-flower.jpg';
  if (imagePath.startsWith('http')) return imagePath;
  return `${process.env.REACT_APP_API_URL?.replace('/api', '')}${imagePath}`;
};

export const getStatusColor = (status) => {
  const colors = {
    pending: 'warning',
    confirmed: 'info',
    processing: 'info',
    shipped: 'info',
    delivered: 'success',
    cancelled: 'error',
  };
  return colors[status] || 'info';
};

export const extractErrorMessage = (error) => {
  const data = error?.response?.data;
  if (!data) return i18n.t('common.genericError');
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const firstKey = Object.keys(data)[0];
  if (firstKey) {
    const msg = data[firstKey];
    return Array.isArray(msg) ? msg[0] : msg;
  }
  return i18n.t('common.genericError');
};
