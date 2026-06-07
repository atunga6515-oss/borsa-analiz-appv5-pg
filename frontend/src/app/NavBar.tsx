"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import api from "@/lib/api";

const NAV_LINKS = [
    { href: "/", label: "Piyasalar", icon: "📊" },
    { href: "/screener", label: "Screener", icon: "⚡" },
    { href: "/portfolio", label: "Portföy", icon: "💼" },
    { href: "/top-picks", label: "Seçki", icon: "🎯" },
    { href: "/analysis", label: "Analiz", icon: "🔬" },
    { href: "/kap", label: "KAP", icon: "📰" },
    { href: "/backtest", label: "Backtest", icon: "⚙️" },
    { href: "/strategy-compare", label: "Kıyasla", icon: "🧪" },
    { href: "/risk", label: "Risk", icon: "⚠️" },
    { href: "/alarms", label: "Alarm", icon: "🔔" },
];

export default function NavBar() {
    const router = useRouter();
    const pathname = usePathname();
    const [username, setUsername] = useState<string | null>(null);
    const [role, setRole] = useState<string | null>(null);
    const [aiQuota, setAiQuota] = useState<number | null>(null);

    useEffect(() => {
        // Cookie-based auth: /auth/me ile username, rol ve kota senkronize edilir
        api.get('/auth/me')
            .then(res => {
                if (res.data) {
                    setUsername(res.data.username || null);
                    setRole(res.data.role || null);
                    setAiQuota(res.data.ai_quota ?? null);
                    // localStorage'ı UI ön belleği olarak güncelle
                    if (res.data.username) localStorage.setItem("username", res.data.username);
                    if (res.data.role) localStorage.setItem("role", res.data.role);
                }
            })
            .catch(() => {
                // Cookie geçersiz/süresi dolmuş — NavBar'da giriş yap göster
                setUsername(null);
                setRole(null);
                setAiQuota(null);
                localStorage.removeItem("username");
                localStorage.removeItem("role");
            });
    }, [pathname]);

    const handleLogout = async () => {
        try {
            await api.post("/auth/logout");
        } catch (e) {
            console.error("Logout error", e);
        }
        
        localStorage.removeItem("username");
        localStorage.removeItem("role");

        setUsername(null);
        setRole(null);
        setAiQuota(null);
        router.push("/");
    };

    const isAuthPage = pathname === "/login" || pathname === "/register";
    if (isAuthPage) return null;

    return (
        <header className="glass-header h-16 flex items-center px-6 sticky top-0 z-50 justify-between">
            <div className="flex items-center gap-8">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-[var(--color-b-yellow)] flex items-center justify-center font-bold text-[#181a20]">
                        V5
                    </div>
                    <span className="text-xl font-bold text-white tracking-tight">Terminal</span>
                </div>
                <nav className="hidden md:flex gap-1">
                    {NAV_LINKS.map((link) => {
                        const isActive = pathname === link.href;
                        return (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={`flex items-center gap-2 px-3 py-2 rounded text-sm font-medium transition-colors ${
                                    isActive
                                        ? "bg-[var(--color-b-panel)] border border-[var(--color-b-yellow)] text-[var(--color-b-yellow)]"
                                        : "border border-transparent text-[var(--color-b-muted)] hover:bg-[var(--color-b-panel)] hover:border-[var(--color-b-border)] hover:text-white"
                                }`}
                            >
                                <span>{link.icon}</span>
                                <span>{link.label}</span>
                            </Link>
                        );
                    })}
                    {role === "admin" && (
                        <a
                            href="/panel"
                            className={`flex items-center gap-2 px-3 py-2 rounded text-sm font-bold transition-colors ${
                                pathname.startsWith("/panel")
                                    ? "bg-purple-900/60 border border-purple-500 text-purple-300"
                                    : "border border-transparent text-purple-400 hover:bg-purple-900/30 hover:border-purple-700 hover:text-purple-300"
                            }`}
                        >
                            <span>⚙️</span>
                            <span>Admin</span>
                        </a>
                    )}
                </nav>
            </div>
            <div className="flex items-center gap-3">
                {username ? (
                    <>
                        {aiQuota !== null && (
                            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-900/30 border border-blue-700/50 text-blue-300 text-xs font-bold cursor-help" title="Yapay Zeka Analiz Krediniz">
                                <span>🤖</span>
                                <span>AI: {aiQuota}</span>
                            </div>
                        )}
                        {role === "admin" && (
                            <a
                                href="/panel"
                                className="hidden sm:flex text-sm items-center gap-1 px-3 py-1.5 rounded bg-purple-900/30 border border-purple-600/50 text-purple-300 hover:bg-purple-900/60 hover:text-white transition-colors"
                            >
                                ⚙️ <span className="font-semibold">Admin Paneli</span>
                            </a>
                        )}
                        <span className="text-[var(--color-b-muted)] text-sm hidden sm:inline">
                            👤 <span className="text-white font-semibold">{username}</span>
                        </span>
                        <button
                            onClick={handleLogout}
                            className="text-sm px-3 py-1.5 rounded border border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:border-red-500 hover:text-red-400 transition-colors"
                        >
                            Çıkış
                        </button>
                    </>
                ) : (
                    <>
                        <Link
                            href="/login"
                            className="bg-[var(--color-b-yellow)] text-[#181a20] px-4 py-1.5 rounded font-semibold text-sm hover:bg-[#f0c929] transition-colors"
                        >
                            Giriş Yap
                        </Link>
                    </>
                )}
            </div>
        </header>
    );
}
