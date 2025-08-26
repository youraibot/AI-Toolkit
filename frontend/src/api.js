import axios from 'axios';

const API_URL = 'http://localhost:5000/api/v1';

const api = axios.create({
    baseURL: API_URL,
});

// Add a request interceptor to include the token in all requests
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;
