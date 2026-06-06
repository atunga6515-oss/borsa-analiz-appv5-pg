"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function LoginPage() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!username || !password) {
            setError("Kullanıcı adı ve şifre boş bırakılamaz.");
            return;
        }
        setLoading(true);
        setError("");
        try {
            const formData = new FormData();
            formData.append("username", username);
            formData.append("password", password);

            const res = await api.post("/auth/token", formData, {
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
            });

            localStorage.setItem("token", res.data.access_token);
            localStorage.setItem("username", res.data.username || username);
            localStorage.setItem("role", res.data.role || "user");
            
            // Set cookie for Next.js middleware
            document.cookie = `token=${res.data.access_token}; path=/; max-age=86400`;

            router.push("/");
        } catch (err: any) {
            setError(
                err?.response?.data?.detail || "Giriş başarısız. Kullanıcı adı veya şifre hatalı."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-[var(--color-b-bg)] relative overflow-hidden">
            {/* Decorative background */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[var(--color-b-yellow)] opacity-5 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-blue-500 opacity-5 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 w-full max-w-md px-6">
                {/* Logo */}
                <div className="text-center mb-10">
                    <div className="inline-flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-[var(--color-b-yellow)] flex items-center justify-center font-black text-[#181a20] text-xl shadow-lg shadow-[rgba(252,213,53,0.3)]">
                            V5
                        </div>
                        <span className="text-3xl font-black text-white tracking-tight">Borsa Terminal</span>
                    </div>
                    <p className="text-[var(--color-b-muted)] text-sm">
                        Profesyonel Hisse Senedi Analiz Platformu
                    </p>
                </div>

                {/* Card */}
                <div className="glass-panel p-8 rounded-2xl border border-[var(--color-b-border)] shadow-2xl">
                    <h2 className="text-2xl font-bold text-white mb-1">Giriş Yap</h2>
                    <p className="text-[var(--color-b-muted)] text-sm mb-6">
                        Hesabınıza erişin
                    </p>

                    <form onSubmit={handleLogin} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-[var(--color-b-muted)] mb-2">
                                Kullanıcı Adı
                            </label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="kullanici_adi"
                                className="w-full px-4 py-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-[var(--color-b-yellow)] transition-colors"
                                autoComplete="username"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-[var(--color-b-muted)] mb-2">
                                Şifre
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="w-full px-4 py-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-[var(--color-b-yellow)] transition-colors"
                                autoComplete="current-password"
                            />
                        </div>

                        {error && (
                            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm flex items-center gap-2">
                                <span>⚠️</span> {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 bg-[var(--color-b-yellow)] text-[#181a20] font-bold rounded-lg hover:bg-[#f0c929] transition-colors disabled:opacity-60 text-base shadow-lg shadow-[rgba(252,213,53,0.2)]"
                        >
                            {loading ? "Giriş yapılıyor..." : "Giriş Yap →"}
                        </button>
                    </form>

                    <div className="mt-6 pt-6 border-t border-[var(--color-b-border)] text-center">
                        <p className="text-[var(--color-b-muted)] text-sm">
                            Sisteme kayıt olmak için yöneticinizle iletişime geçin.
                        </p>
                    </div>
                </div>

                <p className="text-center text-xs text-gray-700 mt-6">
                    Borsa Terminali V5 · Tüm hakları saklıdır.
                </p>
            </div>
        </div>
    );
}
