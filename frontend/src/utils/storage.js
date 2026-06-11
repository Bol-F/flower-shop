const ACCESS_TOKEN_KEY = 'bloom_access_token';
const REFRESH_TOKEN_KEY = 'bloom_refresh_token';

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);

export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);

export const setTokens = (access, refresh) => {
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
};

export const setAccessToken = (access) => {
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
};

export const clearTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};
