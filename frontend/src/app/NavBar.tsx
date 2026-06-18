"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import api from "@/lib/api";

const NAV_GROUPS = [
    {
        title: "Piyasa & Haberler",
        links: [
            { href: "/markets", label: "Piyasalar", icon: "📊", tooltip: "Genel piyasa durumu, endeksler ve anlık takipler. Günlük özetleri inceleyin." },
            { href: "/heatmap", label: "Heatmap", icon: "🗺️", tooltip: "Borsanın genel durumunu sektörlere göre ısı haritası üzerinden görselleştirin." },
            { href: "/kap", label: "KAP", icon: "📰", tooltip: "Şirketlerin Kamuyu Aydınlatma Platformu (KAP) bildirimlerini anlık takip edin." },
        ]
    },
    {
        title: "Tarama & Fırsatlar",
        links: [
            { href: "/screener", label: "Screener", icon: "⚡", tooltip: "Tüm BIST hisselerini temel ve teknik kriterlere göre saniyeler içinde tarayın." },
            { href: "/top-picks-15d", label: "Seçki 15G", icon: "🚀", tooltip: "Sadece kısa vadeli (15 günlük) patlama potansiyeli arayan özel tarama motoru." },
            { href: "/top-picks", label: "Seçki O-U Vade", icon: "🎯", tooltip: "100+ teknik indikatörle analiz edilen orta ve uzun vadeli potansiyelli hisseleri görün." },
            { href: "/alpharank", label: "AlphaRank", icon: "📈", tooltip: "Takip listenizdeki hisseleri 15 günlük yükseliş potansiyellerine göre sıralayın." },
        ]
    },
    {
        title: "Derin Analiz & Test",
        links: [
            { href: "/analysis", label: "Analiz", icon: "🔬", tooltip: "Bir hissenin 100 günlük teknik ve temel detaylarını derinlemesine inceleyin." },
            { href: "/indicators", label: "Pro Terminal", icon: "📈", tooltip: "Seçtiğiniz hisseleri İzleme Listenizde toplayın ve gelişmiş teknik indikatörlerle grafik üzerinde inceleyin." },
            { href: "/backtest", label: "Backtest", icon: "⚙️", tooltip: "Geçmiş verilere dayanarak indikatörlerin al-sat stratejilerini test edin." },
            { href: "/strategy-compare", label: "Kıyasla", icon: "🧪", tooltip: "Farklı al-sat stratejilerinin geçmiş getiri performanslarını birbiriyle kıyaslayın." },
            { href: "/robot", label: "Robot", icon: "🤖", tooltip: "Otonom Al-Sat Robotu (Paper Trading) ile stratejinizi test edin." },
            { href: "/risk", label: "Risk", icon: "⚠️", tooltip: "Portföyünüzün ve piyasanın risk durumunu, volatilite oranlarını analiz edin." },
            { href: "/smc", label: "SMC", icon: "📐", tooltip: "Akıllı Para Konseptleri (Smart Money Concepts) ile market yapısı kırılımlarını (BOS) ve likidite seviyelerini inceleyin." },
        ]
    },
    {
        title: "Hesap Yönetimi",
        links: [
            { href: "/portfolio", label: "Portföy", icon: "💼", tooltip: "Sanal portföyünüzü oluşturun, işlemlerinizi kaydedin. Kâr/zarar durumunuzu takip edin." },
            { href: "/alarms", label: "Alarm", icon: "🔔", tooltip: "Fiyat veya teknik indikatör hedefleri belirleyin. Gerçekleştiğinde bildirim alın." },
        ]
    }
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
                // Cookie/Token geçersiz/süresi dolmuş — NavBar'da giriş yap göster
                setUsername(null);
                setRole(null);
                setAiQuota(null);
                localStorage.removeItem("token");
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
        
        localStorage.removeItem("token");
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
                <Link href="/" className="flex items-center gap-2 cursor-pointer group">
                    <div className="w-8 h-8 rounded bg-gradient-to-br from-[var(--color-b-yellow)] to-yellow-600 flex items-center justify-center font-bold text-[#181a20] group-hover:scale-105 transition-transform text-lg shadow-[0_0_15px_rgba(240,201,41,0.3)]">
                        α
                    </div>
                    <span className="text-xl font-extrabold text-white tracking-tight group-hover:text-[var(--color-b-yellow)] transition-colors">
                        Alfa<span className="text-[var(--color-b-yellow)] font-normal">BIST</span>
                    </span>
                </Link>
                <nav className="hidden md:flex gap-4 items-center">
                    {NAV_GROUPS.map((group, gIdx) => {
                        const isGroupActive = group.links.some(link => pathname === link.href);
                        return (
                            <div key={gIdx} className="group/dropdown relative h-16 flex items-center">
                                {/* Dropdown Header */}
                                <button className={`flex items-center gap-1.5 px-3 py-2 rounded text-sm font-semibold transition-colors ${
                                    isGroupActive ? "text-[var(--color-b-yellow)]" : "text-[var(--color-b-muted)] hover:text-white"
                                }`}>
                                    {group.title}
                                    <span className="text-[10px] opacity-50 group-hover/dropdown:rotate-180 transition-transform duration-200">▼</span>
                                </button>

                                {/* Dropdown Menu */}
                                <div className="absolute top-[60px] left-0 w-56 p-2 bg-[#1e2329] border border-[var(--color-b-border)] rounded-lg shadow-[0_10px_40px_rgba(0,0,0,0.8)] opacity-0 invisible group-hover/dropdown:opacity-100 group-hover/dropdown:visible transition-all duration-200 z-[100] transform translate-y-2 group-hover/dropdown:translate-y-0">
                                    {group.links.map((link) => {
                                        const isActive = pathname === link.href;
                                        return (
                                            <Link
                                                key={link.href}
                                                href={link.href}
                                                className={`group/link relative flex items-center gap-2.5 px-3 py-2.5 rounded text-sm font-medium transition-colors ${
                                                    isActive
                                                        ? "bg-[var(--color-b-panel)] text-[var(--color-b-yellow)]"
                                                        : "text-[var(--color-b-muted)] hover:bg-[#2b3139] hover:text-white"
                                                }`}
                                            >
                                                <span className="text-lg">{link.icon}</span>
                                                <span>{link.label}</span>
                                                
                                                {/* Modern Hover Card (Opens to the right side of the dropdown) */}
                                                <div className="absolute top-0 left-full ml-3 w-64 p-3 bg-[#1e2329]/95 backdrop-blur-xl border border-[var(--color-b-border)] rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.5)] opacity-0 invisible group-hover/link:opacity-100 group-hover/link:visible transition-all duration-300 z-[110] pointer-events-none transform translate-x-2 group-hover/link:translate-x-0">
                                                    {/* Sol taraftaki küçük ok (triangle) */}
                                                    <div className="absolute top-3 -left-2 border-[6px] border-transparent border-r-[#1e2329]/95"></div>
                                                    
                                                    <div className="flex items-center gap-2 mb-1.5 border-b border-[#2b3139] pb-1.5">
                                                        <span className="text-xl">{link.icon}</span>
                                                        <h4 className="text-white font-bold text-sm tracking-wide">{link.label}</h4>
                                                    </div>
                                                    <p className="text-xs text-gray-300 leading-relaxed whitespace-normal">
                                                        {link.tooltip}
                                                    </p>
                                                </div>
                                            </Link>
                                        );
                                    })}
                                </div>
                            </div>
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
