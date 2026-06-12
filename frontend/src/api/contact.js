import apiClient from './axios';

export const sendMessage = (subject, body) =>
  apiClient.post('/contact/send/', { subject, body });

export const getMyMessages = () => apiClient.get('/contact/my-messages/');

// Admin
export const getAdminMessages = (page = 1) =>
  apiClient.get('/contact/admin/messages/', { params: { page, page_size: 100 } });

export const replyToMessage = (id, adminReply) =>
  apiClient.patch(`/contact/admin/messages/${id}/`, { admin_reply: adminReply });

export const markMessageRead = (id) =>
  apiClient.patch(`/contact/admin/messages/${id}/`, { is_read: true });
