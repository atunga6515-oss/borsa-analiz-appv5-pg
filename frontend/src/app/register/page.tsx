"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function RegisterPage() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (!username || !password) {
            setError("Kullanıcı adı ve şifre boş bırakılamaz.");
            return;
        }
        if (password !== confirm) {
            setError("Şifreler eşleşmiyor.");
            return;
        }
        if (password.length < 6) {
            setError("Şifre en az 6 karakter olmalıdır.");
            return;
        }

        setLoading(true);
        try {
            await api.post("/auth/register", { username, password });
            // Kayıt başarılı - giriş sayfasına yönlendir
            router.push("/login?registered=1");
        } catch (err: any) {
            const status = err?.response?.status;
            if (status === 403) {
                setError("Bu sayfaya erişmek için admin yetkisine ihtiyacınız var. Giriş yapmanız gerekiyor.");
            } else {
                setError(
                    err?.response?.data?.detail || "Kayıt başarısız. Lütfen tekrar deneyin."
                );
            }
        } finally {
            setLoading(false);
        }
    };

    const strength = password.length === 0 ? 0 : password.length < 6 ? 1 : password.length < 10 ? 2 : 3;
    const strengthColors = ["", "bg-red-500", "bg-yellow-500", "bg-green-500"];
    const strengthLabels = ["", "Zayıf", "Orta", "Güçlü"];

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-[var(--color-b-bg)] relative overflow-hidden">
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-[var(--color-b-yellow)] opacity-5 rounded-full blur-3xl" />
                <div className="absolute bottom-1/3 left-1/4 w-64 h-64 bg-purple-500 opacity-5 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 w-full max-w-md px-6">
                <div className="text-center mb-10">
                    <div className="inline-flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-[var(--color-b-yellow)] flex items-center justify-center font-black text-[#181a20] text-xl shadow-lg shadow-[rgba(252,213,53,0.3)]">
                            V5
                        </div>
                        <span className="text-3xl font-black text-white tracking-tight">Borsa Terminal</span>
                    </div>
                    <p className="text-[var(--color-b-muted)] text-sm">
                        Yeni hesap oluşturun
                    </p>
                </div>

                <div className="glass-panel p-8 rounded-2xl border border-[var(--color-b-border)] shadow-2xl">
                    <h2 className="text-2xl font-bold text-white mb-1">Yeni Kullanıcı Ekle</h2>
                    <p className="text-[var(--color-b-muted)] text-sm mb-2">
                        Bu sayfa sadece admin yetkisiyle erişilebilir.
                    </p>
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg px-4 py-2 text-yellow-400 text-xs mb-5">
                        ⚠️ Kayıt işlemi admin oturumu gerektirir. Kayıt sonrası kullanıcı giriş yapabilir.
                    </div>

                    <form onSubmit={handleRegister} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-[var(--color-b-muted)] mb-2">
                                Kullanıcı Adı
                            </label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value.toLowerCase().replace(/\s/g, ""))}
                                placeholder="kullanici_adi"
                                className="w-full px-4 py-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-[var(--color-b-yellow)] transition-colors"
                                autoComplete="username"
                            />
                            <p className="text-xs text-gray-600 mt-1">En az 3 karakter, boşluk kullanılamaz</p>
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
                                autoComplete="new-password"
                            />
                            {password.length > 0 && (
                                <div className="mt-2 flex items-center gap-2">
                                    <div className="flex gap-1 flex-1">
                                        {[1, 2, 3].map((i) => (
                                            <div
                                                key={i}
                                                className={`h-1 flex-1 rounded-full transition-all ${i <= strength ? strengthColors[strength] : "bg-[var(--color-b-border)]"}`}
                                            />
                                        ))}
                                    </div>
                                    <span className="text-xs text-gray-400">{strengthLabels[strength]}</span>
                                </div>
                            )}
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-[var(--color-b-muted)] mb-2">
                                Şifre Tekrar
                            </label>
                            <input
                                type="password"
                                value={confirm}
                                onChange={(e) => setConfirm(e.target.value)}
                                placeholder="••••••••"
                                className={`w-full px-4 py-3 bg-[#1e2329] border rounded-lg text-white placeholder-gray-600 focus:outline-none transition-colors ${
                                    confirm && confirm !== password
                                        ? "border-red-500 focus:border-red-500"
                                        : confirm && confirm === password
                                        ? "border-green-500 focus:border-green-500"
                                        : "border-[var(--color-b-border)] focus:border-[var(--color-b-yellow)]"
                                }`}
                                autoComplete="new-password"
                            />
                            {confirm && confirm !== password && (
                                <p className="text-xs text-red-400 mt-1">Şifreler eşleşmiyor</p>
                            )}
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
                            {loading ? "Hesap oluşturuluyor..." : "Kayıt Ol ve Başla →"}
                        </button>
                    </form>

                    <div className="mt-6 pt-6 border-t border-[var(--color-b-border)] text-center">
                        <p className="text-[var(--color-b-muted)] text-sm">
                            Zaten hesabınız var mı?{" "}
                            <Link
                                href="/login"
                                className="text-[var(--color-b-yellow)] hover:underline font-semibold"
                            >
                                Giriş Yap
                            </Link>
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
