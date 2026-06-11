import apiClient from './axios';

export const getOrders = () => apiClient.get('/orders/');

export const getOrder = (id) => apiClient.get(`/orders/${id}/`);

export const createOrder = (data) => apiClient.post('/orders/create/', data);

export const updateOrderStatus = (id, status) =>
  apiClient.patch(`/orders/${id}/status/`, { status });
