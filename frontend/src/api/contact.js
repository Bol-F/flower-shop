import apiClient from './axios';

export const sendMessage = (subject, body) =>
  apiClient.post('/contact/send/', { subject, body });

export const getMyMessages = () => apiClient.get('/contact/my-messages/');
