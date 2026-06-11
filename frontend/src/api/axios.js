import axios from 'axios';
import { getAccessToken, getRefreshToken, setAccessToken, clearTokens } from '../utils/storage';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach access token to every request
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh token on 401 response
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = getRefreshToken();
        const { data } = await axios.post(`${API_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });
        setAccessToken(data.access);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return apiClient(originalRequest);
      } catch {
        clearTokens();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
