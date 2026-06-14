import axios from 'axios';

const api = axios.create({
  baseURL: (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api',
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
