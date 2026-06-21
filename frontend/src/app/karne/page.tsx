"use client";
import { useState, useEffect } from "react";
import api from "@/lib/api";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import toast from "react-hot-toast";

type Bucket = { count: number; win_rate: number; avg_return: number };
type Summary = {
    overall: Bucket;
    bands: { guclu_al: Bucket; al: Bucket; orta: Bucket; dusuk: Bucket };
    bull_flag: Bucket;
    no_bull_flag: Bucket;
    scored_count: number;
    pending_count: number;
};

type LiveBucket = { count: number; avg_return: number; in_profit_pct: number };
type Live = {
    overall: LiveBucket;
    week1: LiveBucket;
    week2: LiveBucket;
    week3: LiveBucket;
    tracked: number;
};

const winColor = (w: number) =>
    w >= 60 ? "text-green-400" : w >= 50 ? "text-yellow-400" : "text-red-400";
const retColor = (r: number) =>
    r > 0 ? "text-green-400" : r < 0 ? "text-red-400" : "text-[var(--color-b-muted)]";

export default function KarnePage() {
    const { AuthModal } = useRequireAuth();
    const [data, setData] = useState<Summary | null>(null);
    const [live, setLive] = useState<Live | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [s, l] = await Promise.allSettled([
                api.get("/scorecard/summary"),
                api.get("/scorecard/live"),
            ]);
            if (s.status === "fulfilled") setData(s.value.data);
            else toast.error("Karne verisi alınamadı.");
            if (l.status === "fulfilled") setLive(l.value.data);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    const Card = ({ title, b, hint }: { title: string; b: Bucket; hint?: string }) => (
        <div className="glass-panel p-4 rounded-lg border border-[var(--color-b-border)]">
            <div className="text-sm text-[var(--color-b-muted)] mb-1">{title}</div>
            <div className="flex items-end gap-3">
                <div>
                    <div className={`text-2xl font-bold ${winColor(b.win_rate)}`}>%{b.win_rate}</div>
                    <div className="text-[10px] text-[var(--color-b-muted)]">isabet</div>
                </div>
                <div>
                    <div className={`text-xl font-semibold ${retColor(b.avg_return)}`}>
                        {b.avg_return > 0 ? "+" : ""}{b.avg_return}%
                    </div>
                    <div className="text-[10px] text-[var(--color-b-muted)]">ort. getiri</div>
                </div>
                <div className="ml-auto text-right">
                    <div className="text-lg font-semibold text-white">{b.count}</div>
                    <div className="text-[10px] text-[var(--color-b-muted)]">sinyal</div>
                </div>
            </div>
            {hint && <div className="text-[11px] text-[var(--color-b-muted)] mt-2">{hint}</div>}
        </div>
    );

    const LiveCard = ({ title, b }: { title: string; b: LiveBucket }) => (
        <div className="glass-panel p-4 rounded-lg border border-[var(--color-b-border)]">
            <div className="text-sm text-[var(--color-b-muted)] mb-1">{title}</div>
            <div className="flex items-end gap-3">
                <div>
                    <div className={`text-2xl font-bold ${retColor(b.avg_return)}`}>
                        {b.avg_return > 0 ? "+" : ""}{b.avg_return}%
                    </div>
                    <div className="text-[10px] text-[var(--color-b-muted)]">anlık ort. getiri</div>
                </div>
                <div>
                    <div className={`text-xl font-semibold ${winColor(b.in_profit_pct)}`}>%{b.in_profit_pct}</div>
                    <div className="text-[10px] text-[var(--color-b-muted)]">şu an kârda</div>
                </div>
                <div className="ml-auto text-right">
                    <div className="text-lg font-semibold text-white">{b.count}</div>
                    <div className="text-[10px] text-[var(--color-b-muted)]">sinyal</div>
                </div>
            </div>
        </div>
    );

    return (
        <>
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="flex justify-between items-end mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🏅 Sinyal Karnesi</h1>
                    <p className="text-[var(--color-b-muted)] max-w-3xl">
                        Seçki 15G'nin ürettiği sinyaller her gün otomatik kaydedilir ve 15 işlem günü sonra
                        gerçek getirisiyle puanlanır. Bu sayfa modelin <strong>gerçek isabet oranını</strong> ve
                        ortalama getirisini skor bandına göre gösterir — yani tahmin değil, ölçüm.
                    </p>
                </div>
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className="px-4 py-2 h-[42px] bg-[#1e2329] border border-[var(--color-b-border)] text-white rounded hover:border-[var(--color-b-yellow)] transition-colors"
                >
                    {loading ? "Yükleniyor…" : "↻ Yenile"}
                </button>
            </div>

            {loading ? (
                <div className="flex-1 flex items-center justify-center text-[var(--color-b-muted)]">
                    <div className="animate-spin text-4xl">⏳</div>
                </div>
            ) : (
                <div className="space-y-8">
                    {/* Anlık Durum (Devam Eden Sinyaller) */}
                    {live && live.tracked > 0 && (
                        <div>
                            <h3 className="text-lg font-semibold text-white mb-2">📈 Devam Eden Sinyaller (Anlık)</h3>
                            <p className="text-xs text-[var(--color-b-muted)] mb-3">
                                Vadesi dolmamış sinyallerin <strong>şu ana kadarki</strong> (gerçekleşmemiş) getirisi — 15 işlem günü beklemeden nasıl gittiğini gösterir. Canlıdır, her gün oynar; nihai sonuç değildir.
                            </p>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <LiveCard title="Tümü (devam eden)" b={live.overall} />
                                <LiveCard title="1. Hafta (0-5 gün)" b={live.week1} />
                                <LiveCard title="2. Hafta (5-10 gün)" b={live.week2} />
                                <LiveCard title="3. Hafta (10+ gün)" b={live.week3} />
                            </div>
                        </div>
                    )}

                    {/* Nihai Karne */}
                    {(!data || data.scored_count === 0) ? (
                        <div className="flex flex-col items-center justify-center text-center text-[var(--color-b-muted)] border-2 border-dashed border-[var(--color-b-border)] rounded-lg p-10">
                            <div className="text-5xl mb-3">⏳</div>
                            <h2 className="text-lg font-bold text-white mb-2">Nihai karne henüz boş</h2>
                            <p className="max-w-xl text-sm">
                                Kesinleşmiş (vadesi dolmuş) isabet/getiri, ilk snapshot'tan
                                <strong> ~15 işlem günü</strong> sonra dolmaya başlar. O zamana kadar yukarıdaki "Devam Eden Sinyaller" panelinden anlık durumu izleyebilirsin.
                            </p>
                            <div className="mt-4 px-4 py-2 rounded bg-[#1e2329] border border-[var(--color-b-border)]">
                                Bekleyen (vadesi dolmamış) sinyal: <strong className="text-white">{data?.pending_count ?? 0}</strong>
                            </div>
                        </div>
                    ) : (
                    <div className="space-y-6">
                    {/* Genel */}
                    <div>
                        <h3 className="text-lg font-semibold text-white mb-2">Genel</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Card title="Tüm Sinyaller" b={data.overall} />
                            <div className="glass-panel p-4 rounded-lg border border-[var(--color-b-border)] flex items-center justify-around">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-white">{data.scored_count}</div>
                                    <div className="text-[10px] text-[var(--color-b-muted)]">puanlandı</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-[var(--color-b-yellow)]">{data.pending_count}</div>
                                    <div className="text-[10px] text-[var(--color-b-muted)]">vadesi bekliyor</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Skor Bandına Göre */}
                    <div>
                        <h3 className="text-lg font-semibold text-white mb-2">Skor Bandına Göre</h3>
                        <p className="text-xs text-[var(--color-b-muted)] mb-3">
                            Yüksek skorlu sinyaller gerçekten daha mı isabetli? Skorun ayırt ediciliğini buradan görürsün.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <Card title="🟢 Güçlü Al (skor ≥ 80)" b={data.bands.guclu_al} />
                            <Card title="📈 Al (70–80)" b={data.bands.al} />
                            <Card title="⚖️ Orta (55–70)" b={data.bands.orta} />
                            <Card title="📉 Düşük (< 55)" b={data.bands.dusuk} />
                        </div>
                    </div>

                    {/* Boğa Flaması Etkisi */}
                    <div>
                        <h3 className="text-lg font-semibold text-white mb-2">Boğa Flaması Etkisi</h3>
                        <p className="text-xs text-[var(--color-b-muted)] mb-3">
                            Boğa Flaması formasyonu olan sinyaller, olmayanlardan daha mı başarılı? Formasyonun katkısı.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Card title="🚩 Boğa Flaması olanlar" b={data.bull_flag} />
                            <Card title="Boğa Flaması olmayanlar" b={data.no_bull_flag} />
                        </div>
                    </div>

                    <p className="text-[11px] text-[var(--color-b-muted)] pt-2">
                        * Getiri, sinyal günündeki fiyattan 15 işlem günü sonraki fiyata göre hesaplanır (komisyon hariç).
                        Yatırım tavsiyesi değildir.
                    </p>
                    </div>
                    )}
                </div>
            )}
        </div>
        <AuthModal />
        </>
    );
}
