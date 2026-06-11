import apiClient from './axios';

export const register = (data) => apiClient.post('/auth/register/', data);

export const login = (email, password) =>
  apiClient.post('/auth/login/', { email, password });

export const getProfile = () => apiClient.get('/auth/profile/');

export const updateProfile = (data) => apiClient.patch('/auth/profile/', data);
