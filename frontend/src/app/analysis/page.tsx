"use client";
import { useState, useEffect } from "react";
import api from "@/lib/api";
import TradingChart from "@/components/TradingChart";
import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function AnalysisPage() {
    const { requireAuth, AuthModal } = useRequireAuth();
    const [ticker, setTicker] = useState("THYAO");
    const [data, setData] = useState<any>(null);
    const [chartData, setChartData] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    
    // History State
    const [historyList, setHistoryList] = useState<any[]>([]);
    const [selectedHistoryId, setSelectedHistoryId] = useState("");

    const fetchHistoryList = async () => {
        try {
            const res = await api.get('/analysis/history/list');
            if (res.data && res.data.data) {
                setHistoryList(res.data.data);
            }
        } catch(e) {
            console.error("Geçmiş çekilemedi", e);
        }
    };
    useEffect(() => {
        // Cookie-based auth: token kontrolü yok, interceptor 401 yönetir
        fetchHistoryList();
    }, []);

    const fetchHistoryById = async (id: string) => {
        if (!id) return;
        setLoading(true);
        setError("");
        setData(null);
        setChartData([]);
        try {
            const res = await api.get(`/analysis/history/${id}`);
            if (res.data) {
                setData(res.data);
                // Also fetch chart data for the ticker in history
                if (res.data.ticker) {
                    setTicker(res.data.ticker);
                    const chartRes = await api.get(`/data/ohlcv/${res.data.ticker}?interval=1d&period=1y`);
                    if (chartRes.data && chartRes.data.data) {
                        setChartData(chartRes.data.data);
                    }
                }
            }
        } catch (err: any) {
            console.error("Geçmiş analiz yüklenemedi", err);
            setError("Geçmiş veri çekilirken hata oluştu.");
        } finally {
            setLoading(false);
        }
    };

    const fetchAnalysis = async (symbol: string) => {
        if (!symbol) return;
        setLoading(true);
        setError("");
        setData(null);
        try {
            const res = await api.get(`/analysis/${symbol}`);
            if (res.data && res.data.data) {
                setData(res.data.data);
            }
            // Fetch chart data as well
            const chartRes = await api.get(`/data/ohlcv/${symbol}?interval=1d&period=1y`);
            if (chartRes.data && chartRes.data.data) {
                setChartData(chartRes.data.data);
            } else {
                setChartData([]);
            }
        } catch (err: any) {
            console.error("Analiz yüklenemedi", err);
            setError(err?.response?.data?.detail || "Veriler çekilirken bir hata oluştu.");
        } finally {
            setLoading(false);
            fetchHistoryList(); // Analizden sonra history listesini güncelle
        }
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        requireAuth(() => fetchAnalysis(ticker));
    };

    const getDecisionColor = (decision: string) => {
        if (!decision) return "bg-[var(--color-b-panel)] border-gray-600";
        if (decision.includes("Al") || decision.includes("Lideri") || decision.includes("Pozitif")) return "bg-green-900/40 border-green-500/50 text-green-400";
        if (decision.includes("Sat") || decision.includes("Negatif") || decision.includes("Baskı")) return "bg-red-900/40 border-red-500/50 text-red-400";
        return "bg-blue-900/40 border-blue-500/50 text-blue-400";
    };

    const handleSendTelegram = async () => {
        if (!data) return;
        setLoading(true);
        try {
            const ssot = data.ssot_result || {};
            const risk = ssot.risk || {};
            const msg = `*🚀 ${data.ticker} Analiz Raporu*
*Fiyat:* ${data.current_price} ₺
*Hibrit Skor:* ${ssot.score} | *Güven Skoru:* ${ssot.pgs}
*Stratejik Karar:* ${ssot.decision}

*🛡️ Risk Yönetimi*
*Stop Loss:* ${risk.SL ? risk.SL : "-"} ₺
*İzleyen Stop:* ${risk.TrailingStop ? risk.TrailingStop : "-"} ₺
*Hedef 1:* ${risk.TP1 ? risk.TP1 : "-"} ₺
*Hedef 2:* ${risk.TP2 ? risk.TP2 : "-"} ₺

*🤖 Yapay Zeka Özeti:*
${ssot.summary || "-"}`;

            const res = await api.post("/telegram/send", { message: msg });
            alert(res.data.message || "Başarıyla gönderildi.");
        } catch (err: any) {
            alert(err?.response?.data?.detail || "Gönderilirken bir hata oluştu.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🔬 Kapsamlı Hisse Analizi</h1>
                    <p className="text-[var(--color-b-muted)]">Yapay zeka, 100+ teknik indikatör ve risk algoritmaları ile detaylı profil</p>
                </div>
                <div className="flex flex-col gap-2 items-end">
                    {historyList.length > 0 && (
                        <select 
                            value={selectedHistoryId}
                            onChange={(e) => {
                                const val = e.target.value;
                                setSelectedHistoryId(val);
                                if (val) fetchHistoryById(val);
                            }}
                            className="bg-[#1e2329] border border-gray-700 text-[var(--color-b-muted)] text-sm px-3 py-1.5 rounded focus:outline-none focus:border-[var(--color-b-yellow)] w-[300px]"
                        >
                            <option value="">-- Geçmiş Analizlerim (Son 30) --</option>
                            {historyList.map(h => (
                                <option key={h.id} value={h.id}>
                                    {h.run_date} - {h.ticker}
                                </option>
                            ))}
                        </select>
                    )}
                    <form onSubmit={handleSearch} className="flex gap-2">
                        <input 
                            type="text" 
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value.toUpperCase())}
                            placeholder="Hisse Kodu (Örn: THYAO)"
                            className="bg-[#1e2329] border border-[var(--color-b-border)] rounded-lg px-4 py-2 text-white outline-none focus:border-[var(--color-b-yellow)]"
                        />
                        <button 
                            type="submit"
                            className="bg-[var(--color-b-yellow)] text-black px-6 py-2 rounded-lg font-bold hover:bg-yellow-500 transition-colors disabled:opacity-50"
                            disabled={loading}
                        >
                            {loading ? "..." : "Analiz Et"}
                        </button>
                    </form>
                    {data && (
                        <button 
                            type="button"
                            onClick={() => requireAuth(handleSendTelegram)}
                            className="bg-[#24A1DE] hover:bg-[#1d82b5] text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                            disabled={loading}
                        >
                            📤 Telegram'a Gönder
                        </button>
                    )}
                </div>
            </div>

            {error && (
                <div className="p-4 bg-red-900/50 border border-red-500/50 rounded text-white mb-6">
                    🚨 {error}
                </div>
            )}

            {!data && !loading && !error && (
                <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-b-muted)] border-2 border-dashed border-[var(--color-b-border)] rounded-lg p-12">
                    <div className="text-6xl mb-4">📊</div>
                    <h2 className="text-xl font-bold text-white mb-2">Analiz Bekleniyor</h2>
                    <p>Hisse senedi kodunu girerek derin analizi başlatın.</p>
                </div>
            )}

            {loading && (
                <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-b-muted)] border-2 border-dashed border-[var(--color-b-border)] rounded-lg p-12">
                    <div className="animate-spin text-5xl mb-4">⏳</div>
                    <h2 className="text-xl font-bold text-white mb-2">Yapay Zeka Analizi Çalışıyor</h2>
                    <p>100+ indikatör hesaplanıyor ve haberler yorumlanıyor. Lütfen bekleyin...</p>
                </div>
            )}

            {data && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* LEFT COLUMN: Metrics */}
                    <div className="lg:col-span-1 space-y-6">
                        
                        {/* Premium Card */}
                        <div className="glass-panel p-6 rounded-lg border border-[var(--color-b-border)] bg-gradient-to-br from-[#1e2329] to-[#0d1117]">
                            <div className="flex items-center justify-between mb-4">
                                <div className="text-3xl font-black text-white">{data.ticker}</div>
                                <div className="text-2xl font-bold text-white">{data.current_price?.toFixed(2)} ₺</div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4 mt-6">
                                <div className="bg-[#181a20] p-3 rounded text-center border border-[var(--color-b-border)]">
                                    <div className="text-[var(--color-b-muted)] text-xs mb-1">Hibrit Potansiyel</div>
                                    <div className="text-2xl font-bold text-[var(--color-b-green)]">{data.ssot_result?.score}</div>
                                </div>
                                <div className="bg-[#181a20] p-3 rounded text-center border border-[var(--color-b-border)]">
                                    <div className="text-[var(--color-b-muted)] text-xs mb-1">Güven Skoru (PGS)</div>
                                    <div className="text-2xl font-bold text-[var(--color-b-yellow)]">{data.ssot_result?.pgs}</div>
                                </div>
                            </div>
                        </div>

                        {/* Decision & Conviction */}
                        <div className={`p-4 rounded-lg border ${getDecisionColor(data.ssot_result?.core_decision)}`}>
                            <div className="text-sm uppercase font-bold opacity-80 mb-1">Stratejik Karar (SSOT)</div>
                            <div className="text-2xl font-black">{data.ssot_result?.core_decision || "NÖTR"}</div>
                        </div>

                        <div className="bg-[#1e2329] p-4 rounded-lg border border-[var(--color-b-border)]">
                            <div className="text-sm text-[var(--color-b-muted)] font-bold mb-1">Güven Seviyesi (Conviction)</div>
                            <div className="text-xl font-bold text-white">{data.ssot_result?.conviction_level || "ORTA ⚖️"}</div>
                        </div>

                        {/* Voting Bar */}
                        <div className="bg-[#181a20] p-5 rounded-lg border border-[var(--color-b-border)]">
                            <h3 className="font-bold text-white mb-4">🚦 İndikatör Oylama Dağılımı</h3>
                            <div className="flex gap-2 justify-between mb-2 text-sm font-bold">
                                <span className="text-green-500">🟢 AL: {data.ssot_result?.buy_votes}</span>
                                <span className="text-red-500">🔴 SAT: {data.ssot_result?.sell_votes}</span>
                            </div>
                            {/* Visual Bar */}
                            <div className="w-full h-4 rounded-full bg-gray-800 flex overflow-hidden">
                                <div 
                                    className="bg-green-500 h-full" 
                                    style={{ width: `${(data.ssot_result?.buy_votes / (data.ssot_result?.total_votes || 1)) * 100}%` }}
                                />
                                <div 
                                    className="bg-gray-600 h-full" 
                                    style={{ width: `${((data.ssot_result?.total_votes - data.ssot_result?.buy_votes - data.ssot_result?.sell_votes) / (data.ssot_result?.total_votes || 1)) * 100}%` }}
                                />
                                <div 
                                    className="bg-red-500 h-full" 
                                    style={{ width: `${(data.ssot_result?.sell_votes / (data.ssot_result?.total_votes || 1)) * 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Risk Management */}
                        <div className="bg-[#181a20] p-5 rounded-lg border border-[var(--color-b-border)]">
                            <h3 className="font-bold text-white mb-4">🛡️ Risk Yönetimi (ATR Bazlı)</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <div className="text-[var(--color-b-muted)] text-xs">Stop Loss</div>
                                    <div className="text-red-400 font-bold">{data.ssot_result?.risk?.SL ? data.ssot_result.risk.SL.toFixed(2) : "-"} ₺</div>
                                </div>
                                <div>
                                    <div className="text-[var(--color-b-muted)] text-xs">İzleyen Stop (TS)</div>
                                    <div className="text-orange-400 font-bold">{data.ssot_result?.risk?.TrailingStop ? data.ssot_result.risk.TrailingStop.toFixed(2) : "-"} ₺</div>
                                </div>
                                <div>
                                    <div className="text-[var(--color-b-muted)] text-xs">Hedef 1 (TP1)</div>
                                    <div className="text-green-400 font-bold">{data.ssot_result?.risk?.TP1 ? data.ssot_result.risk.TP1.toFixed(2) : "-"} ₺</div>
                                </div>
                                <div>
                                    <div className="text-[var(--color-b-muted)] text-xs">Hedef 2 (TP2)</div>
                                    <div className="text-blue-400 font-bold">{data.ssot_result?.risk?.TP2 ? data.ssot_result.risk.TP2.toFixed(2) : "-"} ₺</div>
                                </div>
                            </div>
                        </div>

                    </div>

                    {/* RIGHT COLUMN: Chart and Details */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Chart Area */}
                        <div className="glass-panel p-4 rounded-lg h-[400px]">
                            {chartData.length > 0 ? (
                                <TradingChart data={chartData} />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-[var(--color-b-muted)]">
                                    Grafik verisi yükleniyor veya bulunamadı...
                                </div>
                            )}
                        </div>

                        {/* AI Summary */}
                        <div className="bg-[#1e2329] p-5 rounded-lg border-l-4 border-[var(--color-b-yellow)]">
                            <h3 className="font-bold text-white mb-2">🤖 Yapay Zeka Analiz Özeti</h3>
                            <p className="text-[var(--color-b-muted)] text-sm leading-relaxed whitespace-pre-wrap">
                                {data.ssot_result?.summary}
                            </p>
                        </div>

                        {/* Indicator Proof Table */}
                        {data.ssot_result?.core_votes_list && data.ssot_result.core_votes_list.length > 0 && (
                            <div className="glass-panel rounded-lg overflow-hidden">
                                <div className="p-4 bg-[#181a20] border-b border-[var(--color-b-border)]">
                                    <h3 className="font-bold text-white">🔍 İndikatör Kanıtları (Ensemble)</h3>
                                </div>
                                <div className="max-h-[300px] overflow-y-auto">
                                    <table className="w-full text-left text-sm">
                                        <thead className="bg-[#1e2329] text-[var(--color-b-muted)] sticky top-0">
                                            <tr>
                                                <th className="p-3 font-semibold">İndikatör / Kural</th>
                                                <th className="p-3 font-semibold">Durum</th>
                                                <th className="p-3 font-semibold">Etki Ağırlığı</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.ssot_result.core_votes_list.map((vote: any, idx: number) => {
                                                const isAl = vote.Durum?.includes("AL");
                                                const isSat = vote.Durum?.includes("SAT");
                                                return (
                                                    <tr key={idx} className="border-b border-[var(--color-b-border)] hover:bg-[#1e2329]">
                                                        <td className="p-3 text-white">{vote["İndikatör/Kural"]}</td>
                                                        <td className={`p-3 font-bold ${isAl ? 'text-green-500' : isSat ? 'text-red-500' : 'text-gray-400'}`}>
                                                            {vote.Durum}
                                                        </td>
                                                        <td className="p-3 text-[var(--color-b-muted)]">Ağırlık: {vote["Ağırlık Puanı"]}</td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
        <AuthModal />
        </>
    );
}
