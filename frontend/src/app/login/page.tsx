"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const formData = new URLSearchParams();
            formData.append("username", username);
            formData.append("password", password);

            const res = await api.post('/auth/token', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            if (res.data && res.data.access_token) {
                localStorage.setItem('token', res.data.access_token);
                // Başarılı girişte dashboard'a yönlendir
                router.push('/');
                // Auth durumunun yenilenmesi için sayfayı zorla
                setTimeout(() => window.location.reload(), 100);
            }
        } catch (err: any) {
            console.error("Login hatası:", err);
            setError(err.response?.data?.detail || "Giriş başarısız. Lütfen bilgilerinizi kontrol edin.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex w-full min-h-screen items-center justify-center bg-[var(--color-b-bg)] text-[var(--color-b-text)]">
            <div className="glass-panel p-8 rounded-xl w-full max-w-md shadow-2xl border border-[var(--color-b-border)]">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">Giriş Yap</h1>
                    <p className="text-[var(--color-b-muted)]">Borsa Analiz Terminali'ne hoş geldiniz</p>
                </div>

                {error && (
                    <div className="bg-red-500 bg-opacity-20 border border-red-500 text-red-400 p-3 rounded mb-6 text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleLogin} className="flex flex-col gap-5">
                    <div>
                        <label className="block text-sm text-[var(--color-b-muted)] mb-2 font-medium">Kullanıcı Adı</label>
                        <input 
                            type="text" 
                            required 
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white focus:outline-none focus:border-[var(--color-b-yellow)] transition-colors"
                            placeholder="Kullanıcı adınızı girin"
                        />
                    </div>
                    
                    <div>
                        <label className="block text-sm text-[var(--color-b-muted)] mb-2 font-medium">Şifre</label>
                        <input 
                            type="password" 
                            required 
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white focus:outline-none focus:border-[var(--color-b-yellow)] transition-colors"
                            placeholder="••••••••"
                        />
                    </div>

                    <button 
                        type="submit" 
                        disabled={loading}
                        className="w-full mt-4 p-3 bg-[var(--color-b-yellow)] text-black font-bold rounded hover:bg-yellow-500 transition-colors disabled:opacity-50"
                    >
                        {loading ? "Giriş Yapılıyor..." : "Sisteme Gir"}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-[var(--color-b-muted)] text-sm">
                        Henüz hesabınız yok mu? <a href="#" className="text-[var(--color-b-yellow)] hover:underline">Kayıt Ol</a>
                    </p>
                </div>
            </div>
        </div>
    );
}
