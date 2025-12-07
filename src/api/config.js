// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://10.128.7.187:8099',
  TIMEOUT: 30000, // 30 seconds
};

// Storage keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  AUTH_TOKEN: 'authToken', // для обратной совместимости
  TOKEN: 'token', // для обратной совместимости
};

