"use client";
import { useState, useEffect } from "react";
import api from "@/lib/api";

interface StopLossSuggestion {
    ticker: string;
    alis_maliyeti: number;
    anlik_fiyat: number;
    onerilen_stop: number;
    risk_durumu: string;
    adet: number;
}

interface RiskData {
    portfolio_beta: number;
    portfolio_var: number;
    stop_loss_suggestions: StopLossSuggestion[];
}

export default function RiskPage() {
    const [data, setData] = useState<RiskData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchRiskData = async () => {
            try {
                const res = await api.get("/risk/");
                if (res.data.status === "empty") {
                    setData(null);
                    setError(res.data.message);
                } else if (res.data.status === "success") {
                    setData(res.data.data);
                }
            } catch (err: any) {
                setError("Risk verileri yüklenirken bir hata oluştu.");
            } finally {
                setLoading(false);
            }
        };

        fetchRiskData();
    }, []);

    const getBetaDesc = (beta: number) => {
        if (beta === 0) return "Portföyde hisse yok.";
        if (beta < 0.8) return `Piyasadan %${Math.round((1 - beta) * 100)} daha az dalgalı. Defansif bir portföy.`;
        if (beta > 1.2) return `Piyasadan %${Math.round((beta - 1) * 100)} daha hareketli. Agresif bir portföy.`;
        return "Piyasa ile benzer hareket ediyor. Dengeli bir portföy.";
    };

    const getBetaColor = (beta: number) => {
        if (beta < 0.8) return "text-[var(--color-b-green)]";
        if (beta > 1.2) return "text-[var(--color-b-red)]";
        return "text-[var(--color-b-yellow)]";
    };

    const getRiskColor = (risk: string) => {
        if (risk === "Yüksek") return "bg-[var(--color-b-red)]";
        if (risk === "Orta") return "bg-[var(--color-b-yellow)] text-black";
        return "bg-[var(--color-b-green)] text-black";
    };

    return (
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">⚠️ Risk Yönetim Merkezi</h1>
                <p className="text-[var(--color-b-muted)]">Portföyünüzün Volatilite ve Beta Analizleri</p>
            </div>

            {loading && (
                <div className="flex-1 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--color-b-yellow)]"></div>
                </div>
            )}

            {!loading && error && (
                <div className="glass-panel p-8 text-center rounded-xl border border-[var(--color-b-yellow)]/30">
                    <div className="text-4xl mb-4">🛡️</div>
                    <h2 className="text-xl text-white font-bold mb-2">Bilgi Bekleniyor</h2>
                    <p className="text-[var(--color-b-muted)]">{error}</p>
                </div>
            )}

            {!loading && data && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div className="glass-panel p-6 rounded-lg">
                            <h2 className="text-xl font-bold text-white mb-4">Portföy Beta Değeri (Piyasa Riski)</h2>
                            <div className="flex items-center gap-4">
                                <div className={`text-4xl font-bold ${getBetaColor(data.portfolio_beta)}`}>
                                    {data.portfolio_beta.toFixed(2)}
                                </div>
                                <div className="text-sm text-[var(--color-b-muted)]">
                                    {getBetaDesc(data.portfolio_beta)}
                                </div>
                            </div>
                        </div>
                        
                        <div className="glass-panel p-6 rounded-lg">
                            <h2 className="text-xl font-bold text-white mb-4">Maksimum Kayıp İhtimali (VaR)</h2>
                            <div className="flex items-center gap-4">
                                <div className="text-4xl font-bold text-[var(--color-b-red)]">
                                    %{data.portfolio_var.toFixed(2)}
                                </div>
                                <div className="text-sm text-[var(--color-b-muted)]">
                                    Günlük %95 güven aralığında geçmiş verilere dayalı tahmini maksimum kayıp yüzdesi.
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="glass-panel p-6 rounded-lg mb-6">
                        <h2 className="text-xl font-bold text-white mb-4">Aktif İşlemler İçin Dinamik Stop-Loss Önerileri (ATR)</h2>
                        
                        {data.stop_loss_suggestions.length === 0 ? (
                            <p className="text-[var(--color-b-muted)]">Analiz edilecek aktif işlem bulunamadı.</p>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead className="bg-[#1e2329] text-[var(--color-b-muted)] text-sm whitespace-nowrap">
                                        <tr>
                                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Hisse</th>
                                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Adet</th>
                                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Alış Maliyeti</th>
                                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Anlık Fiyat</th>
                                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Önerilen Stop</th>
                                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Risk Durumu</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.stop_loss_suggestions.map((item, idx) => (
                                            <tr key={idx} className="hover:bg-[#1e2329] transition-colors border-b border-[var(--color-b-border)]">
                                                <td className="p-4 font-bold text-white">{item.ticker}</td>
                                                <td className="p-4 text-[var(--color-b-muted)]">{item.adet}</td>
                                                <td className="p-4 text-white">₺{item.alis_maliyeti.toFixed(2)}</td>
                                                <td className={`p-4 font-bold ${item.anlik_fiyat >= item.alis_maliyeti ? 'text-[var(--color-b-green)]' : 'text-[var(--color-b-red)]'}`}>
                                                    ₺{item.anlik_fiyat.toFixed(2)}
                                                </td>
                                                <td className="p-4 text-[var(--color-b-yellow)] font-bold">₺{item.onerilen_stop.toFixed(2)}</td>
                                                <td className="p-4">
                                                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getRiskColor(item.risk_durumu)}`}>
                                                        {item.risk_durumu}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}
