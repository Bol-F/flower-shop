import apiClient from './axios';

export const getCart = () => apiClient.get('/cart/');

export const addToCart = (productId, quantity = 1) =>
  apiClient.post('/cart/items/', { product_id: productId, quantity });

export const updateCartItem = (productId, quantity) =>
  apiClient.patch(`/cart/items/${productId}/`, { quantity });

export const removeFromCart = (productId) =>
  apiClient.delete(`/cart/items/${productId}/`);

export const clearCart = () => apiClient.delete('/cart/');
