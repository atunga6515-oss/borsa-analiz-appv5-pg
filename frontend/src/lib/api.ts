import axios from 'axios';

const api = axios.create({
  baseURL: (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api',
  withCredentials: true,
});

// Otomatik token ekleme (Geriye dönük uyumluluk ve cross-origin HTTP desteği için)
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Hata yakalama
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (typeof window !== 'undefined') {
        // Oturum süresi dolmuş veya geçersiz token
        // Eğer kullanıcı ana sayfadaysa (dashboard) yönlendirme yapma.
        // Başka bir özelliğe (sayfaya) tıklayıp geldiyse login'e yönlendir ve mesaj ekle.
        if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
          window.location.href = '/login?msg=test_features';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
