import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for unified error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const customError = {
      message: error.response?.data?.detail || error.message || 'An unexpected error occurred.',
      status: error.response?.status,
      data: error.response?.data,
    };
    return Promise.reject(customError);
  }
);
