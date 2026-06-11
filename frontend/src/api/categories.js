import apiClient from './axios';

export const getCategories = () => apiClient.get('/categories/');

export const getCategory = (slug) => apiClient.get(`/categories/${slug}/`);

export const createCategory = (data) => apiClient.post('/categories/', data);

export const updateCategory = (slug, data) =>
  apiClient.patch(`/categories/${slug}/`, data);

export const deleteCategory = (slug) =>
  apiClient.delete(`/categories/${slug}/`);
