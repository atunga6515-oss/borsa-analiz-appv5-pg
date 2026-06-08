"use client";
import Link from "next/link";

const DASHBOARD_MODULES = [
    {
        category: "Piyasa & Haberler",
        items: [
            { href: "/markets", label: "Piyasalar", icon: "📊", desc: "Genel piyasa durumu, BIST100 grafiği, endeksler ve makro takvim.", color: "from-blue-500 to-cyan-500" },
            { href: "/heatmap", label: "Heatmap", icon: "🗺️", desc: "Borsanın genel durumunu ve para giriş/çıkışını sektörlere göre ısı haritası üzerinden görselleştirin.", color: "from-emerald-500 to-teal-400" },
            { href: "/kap", label: "KAP Bildirimleri", icon: "📰", desc: "Şirketlerin Kamuyu Aydınlatma Platformu bildirimlerini yapay zeka ile özetlenmiş şekilde anlık takip edin.", color: "from-gray-500 to-gray-300" },
        ]
    },
    {
        category: "Tarama & Fırsatlar",
        items: [
            { href: "/screener", label: "Screener", icon: "⚡", desc: "Tüm BIST hisselerini 100'den fazla temel ve teknik kritere göre saniyeler içinde filtreleyip tarayın.", color: "from-yellow-500 to-orange-500" },
            { href: "/top-picks", label: "Stratejik Seçki", icon: "🎯", desc: "Teknik indikatörlerin ürettiği AL sinyallerine göre analiz edilen en yüksek potansiyelli hisseleri görün.", color: "from-red-500 to-pink-500" },
            { href: "/alpharank", label: "AlphaRank 15D", icon: "🚀", desc: "Gelişmiş yapay zeka ve makine öğrenimi modeliyle hisseleri 15 günlük yükseliş potansiyellerine göre sıralayın.", color: "from-purple-600 to-indigo-500" },
        ]
    },
    {
        category: "Derin Analiz & Test",
        items: [
            { href: "/analysis", label: "Derin Analiz", icon: "🔬", desc: "Bir hissenin son 100 günlük teknik, takas ve temel detaylarını derinlemesine inceleyin.", color: "from-indigo-500 to-blue-500" },
            { href: "/backtest", label: "Backtest Modülü", icon: "⚙️", desc: "Geçmiş piyasa verilerine dayanarak teknik indikatörlerin al-sat stratejilerini test edin ve kârlılığını ölçün.", color: "from-orange-500 to-red-500" },
            { href: "/strategy-compare", label: "Strateji Kıyasla", icon: "🧪", desc: "Farklı al-sat stratejilerinin geçmiş getiri performanslarını birbiriyle kıyaslayıp en uygununu bulun.", color: "from-pink-500 to-rose-400" },
            { href: "/risk", label: "Risk Analizi", icon: "⚠️", desc: "Portföyünüzün ve piyasanın genel risk durumunu, volatilite oranlarını matematiksel modellerle analiz edin.", color: "from-red-600 to-orange-600" },
        ]
    },
    {
        category: "Hesap Yönetimi",
        items: [
            { href: "/portfolio", label: "Sanal Portföy", icon: "💼", desc: "Kendi sanal portföyünüzü oluşturun, alış/satış işlemlerinizi kaydedip anlık kâr/zarar durumunuzu takip edin.", color: "from-green-500 to-emerald-500" },
            { href: "/alarms", label: "Akıllı Alarmlar", icon: "🔔", desc: "Fiyat veya özel teknik indikatör hedefleri belirleyin. Şartlar gerçekleştiğinde anında bildirim alın.", color: "from-amber-400 to-yellow-500" },
        ]
    }
];

export default function Dashboard() {
    return (
        <div className="p-6 md:p-8 max-w-[1400px] mx-auto min-h-[calc(100vh-64px)]">
            {/* Header Section */}
            <div className="mb-10 text-center md:text-left flex flex-col md:flex-row justify-between items-end gap-4">
                <div>
                    <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[var(--color-b-yellow)] to-yellow-200 mb-4 tracking-tight">
                        V5 Terminal'e Hoş Geldiniz
                    </h1>
                    <p className="text-[var(--color-b-muted)] text-lg max-w-2xl leading-relaxed">
                        Yapay zeka destekli profesyonel borsa analiz platformunuz. 
                        Aşağıdaki modüllerden birini seçerek piyasanın bir adım önüne geçin.
                    </p>
                </div>
                <Link 
                    href="/markets" 
                    className="px-6 py-3 bg-[var(--color-b-yellow)] text-[#181a20] font-bold rounded-lg hover:bg-yellow-400 transition-colors flex items-center gap-2 shadow-[0_0_20px_rgba(240,201,41,0.2)]"
                >
                    <span>📊</span>
                    Piyasalara Git
                </Link>
            </div>

            {/* Modules Grid */}
            <div className="flex flex-col gap-10 pb-12">
                {DASHBOARD_MODULES.map((group, gIdx) => (
                    <div key={gIdx} className="space-y-5">
                        <div className="flex items-center gap-4">
                            <h2 className="text-xl font-bold text-white tracking-wide whitespace-nowrap">{group.category}</h2>
                            <div className="flex-1 h-px bg-gradient-to-r from-[#2b3139] to-transparent"></div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                            {group.items.map((item, iIdx) => (
                                <Link 
                                    href={item.href} 
                                    key={iIdx}
                                    className="group relative overflow-hidden rounded-2xl bg-[#1e2329] border border-[#2b3139] hover:border-[var(--color-b-yellow)] transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.5)] hover:-translate-y-1 flex flex-col h-full min-h-[160px]"
                                >
                                    {/* Gradient Accent Top Bar */}
                                    <div className={`h-1.5 w-full bg-gradient-to-r ${item.color} opacity-80 group-hover:opacity-100 transition-opacity`}></div>
                                    
                                    <div className="p-6 flex flex-col flex-1 z-10 bg-gradient-to-b from-transparent to-[#181a20]/30">
                                        <div className="flex items-center gap-4 mb-3">
                                            <div className="w-12 h-12 rounded-xl bg-[#181a20] border border-[#2b3139] flex items-center justify-center text-2xl group-hover:scale-110 transition-transform duration-300 shadow-inner">
                                                {item.icon}
                                            </div>
                                            <h3 className="font-bold text-lg text-white group-hover:text-[var(--color-b-yellow)] transition-colors leading-tight">
                                                {item.label}
                                            </h3>
                                        </div>
                                        <p className="text-sm text-[var(--color-b-muted)] leading-relaxed flex-1 mt-1">
                                            {item.desc}
                                        </p>
                                    </div>
                                    
                                    {/* Subtly animated background glow on hover */}
                                    <div className={`absolute -bottom-12 -right-12 w-40 h-40 bg-gradient-to-br ${item.color} rounded-full blur-[60px] opacity-0 group-hover:opacity-15 transition-opacity duration-500 pointer-events-none`}></div>
                                </Link>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
