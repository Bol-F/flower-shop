import apiClient from './axios';

export const getProducts = (params = {}) =>
  apiClient.get('/products/', { params });

export const getProduct = (slug) => apiClient.get(`/products/${slug}/`);

export const createProduct = (data) => apiClient.post('/products/', data);

export const updateProduct = (slug, data) =>
  apiClient.patch(`/products/${slug}/`, data);

export const deleteProduct = (slug) => apiClient.delete(`/products/${slug}/`);
