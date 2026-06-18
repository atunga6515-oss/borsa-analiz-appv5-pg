import axios from 'axios';

const getBaseUrl = () => {
  if (typeof window !== 'undefined') {
    return '/api'; // Tarayıcıda her zaman relative path kullan ki origin %100 eşleşsin
  }
  return (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api';
};

const api = axios.create({
  baseURL: getBaseUrl(),
  withCredentials: true,
});

// Auth: HttpOnly cookie ile yönetilir (withCredentials: true).
// localStorage'daki eski token'a güvenilmez; backend her istek için cookie'yi doğrular.

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
          window.location.replace('/login?msg=session_expired');
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
