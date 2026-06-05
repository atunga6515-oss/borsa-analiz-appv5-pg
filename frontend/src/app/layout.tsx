"use client";
import type { Metadata } from "next";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import "./globals.css";

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

function NavBar() {
    const router = useRouter();
    const pathname = usePathname();
    const [username, setUsername] = useState<string | null>(null);

    useEffect(() => {
        if (typeof window !== "undefined") {
            setUsername(localStorage.getItem("username"));
        }
    }, [pathname]);

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        setUsername(null);
        router.push("/login");
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
                    <h1 className="text-xl font-bold text-white tracking-tight">Terminal</h1>
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
                </nav>
            </div>
            <div className="flex items-center gap-3">
                {username ? (
                    <>
                        <span className="text-[var(--color-b-muted)] text-sm">
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
                            className="text-sm px-3 py-1.5 rounded border border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white hover:border-[var(--color-b-yellow)] transition-colors"
                        >
                            Giriş Yap
                        </Link>
                        <Link
                            href="/register"
                            className="bg-[var(--color-b-yellow)] text-[#181a20] px-4 py-1.5 rounded font-semibold text-sm hover:bg-[#f0c929] transition-colors"
                        >
                            Kayıt Ol
                        </Link>
                    </>
                )}
            </div>
        </header>
    );
}

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="tr">
            <body className="antialiased min-h-screen flex flex-col">
                <NavBar />
                <main className="flex-1 flex overflow-hidden">{children}</main>
            </body>
        </html>
    );
}
