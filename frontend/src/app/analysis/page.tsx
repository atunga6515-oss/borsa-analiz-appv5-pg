"use client";
import { useState, useEffect, Suspense } from "react";
import api from "@/lib/api";
import TradingChart from "@/components/TradingChart";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { useSearchParams } from "next/navigation";
import SymbolAutocomplete from "@/components/SymbolAutocomplete";
import toast from 'react-hot-toast';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from "react-resizable-panels";

function AnalysisPageContent() {
    const { requireAuth, AuthModal } = useRequireAuth();
    const [ticker, setTicker] = useState("");
    const [data, setData] = useState<any>(null);
    const [chartData, setChartData] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    
    // History State
    const [historyList, setHistoryList] = useState<any[]>([]);
    const [selectedHistoryId, setSelectedHistoryId] = useState("");
    const [isIndicatorModalOpen, setIsIndicatorModalOpen] = useState(false);

    const searchParams = useSearchParams();

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
        
        const tickerParam = searchParams.get("ticker");
        if (tickerParam) {
            setTicker(tickerParam.toUpperCase());
            requireAuth(() => fetchAnalysis(tickerParam.toUpperCase()));
        }
    }, [searchParams]);

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
            toast.success(res.data.message || "Başarıyla gönderildi.");
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Gönderilirken bir hata oluştu.");
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
                        <SymbolAutocomplete 
                            value={ticker}
                            onChange={(val) => setTicker(val)}
                            className="w-64"
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
                        <div className="flex gap-2 items-center">
                            {data.ssot_result?.core_votes_list && data.ssot_result.core_votes_list.length > 0 && (
                                <button 
                                    onClick={() => setIsIndicatorModalOpen(true)}
                                    className="bg-gradient-to-r from-[#0ea5e9] to-[#06b6d4] hover:from-[#0284c7] hover:to-[#0891b2] border-none text-white px-4 py-2 rounded-lg font-medium shadow-md flex items-center justify-center gap-2 transition-all transform hover:-translate-y-0.5"
                                >
                                    🔍 İndikatör Sinyalleri
                                </button>
                            )}
                            <button 
                                type="button"
                                onClick={() => requireAuth(handleSendTelegram)}
                                className="bg-[#24A1DE] hover:bg-[#1d82b5] text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                                disabled={loading}
                            >
                                📤 Telegram'a Gönder
                            </button>
                        </div>
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
                <div className="flex-1 w-full flex mb-2" style={{ minHeight: "800px", height: "calc(100vh - 160px)" }}>
                    <PanelGroup orientation="horizontal" id="analysis-layout" autoSave="analysis-layout">
                        {/* LEFT COLUMN: Metrics */}
                        <Panel defaultSize={30} minSize={20} className="flex flex-col space-y-6 overflow-y-auto pr-4 pb-4">
                            
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

                        {/* 3'lü Vade Kartları (Time Horizons) */}
                        <div className="bg-[#181a20] p-4 rounded-lg border border-[var(--color-b-border)]">
                            <h3 className="font-bold text-white mb-4">⏳ Vadelere Göre Strateji</h3>
                            
                            {/* Kısa Vade */}
                            <div className="mb-4">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-bold text-[var(--color-b-muted)]">⚡ Kısa Vade (0-15 Gün)</span>
                                    <span className={`font-black ${getDecisionColor(data.ssot_result?.short_term?.decision).replace('bg-', 'text-').replace('/10', '')}`}>{data.ssot_result?.short_term?.decision || "NÖTR"} ({data.ssot_result?.short_term?.score}%)</span>
                                </div>
                                <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-green-500" style={{width: `${data.ssot_result?.short_term?.score || 50}%`}}></div>
                                </div>
                            </div>
                            
                            {/* Orta Vade */}
                            <div className="mb-4">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-bold text-[var(--color-b-muted)]">📅 Orta Vade (1-3 Ay)</span>
                                    <span className={`font-black ${getDecisionColor(data.ssot_result?.medium_term?.decision).replace('bg-', 'text-').replace('/10', '')}`}>{data.ssot_result?.medium_term?.decision || "NÖTR"} ({data.ssot_result?.medium_term?.score}%)</span>
                                </div>
                                <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500" style={{width: `${data.ssot_result?.medium_term?.score || 50}%`}}></div>
                                </div>
                            </div>
                            
                            {/* Uzun Vade */}
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-bold text-[var(--color-b-muted)]">🔭 Uzun Vade (3-12 Ay)</span>
                                    <span className={`font-black ${getDecisionColor(data.ssot_result?.long_term?.decision).replace('bg-', 'text-').replace('/10', '')}`}>{data.ssot_result?.long_term?.decision || "NÖTR"} ({data.ssot_result?.long_term?.score}%)</span>
                                </div>
                                <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-purple-500" style={{width: `${data.ssot_result?.long_term?.score || 50}%`}}></div>
                                </div>
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


                        </Panel>

                        <PanelResizeHandle className="w-1.5 mx-2 bg-gray-800 hover:bg-[var(--color-b-yellow)] rounded transition-colors cursor-col-resize flex flex-col justify-center items-center">
                            <div className="h-8 w-0.5 bg-gray-500 rounded-full"></div>
                        </PanelResizeHandle>

                        {/* RIGHT COLUMN: Chart and Details */}
                        <Panel defaultSize={70} minSize={30}>
                            <PanelGroup orientation="vertical" id="analysis-layout-right" autoSave="analysis-layout-right">
                                {/* Chart Area */}
                                <Panel defaultSize={60} minSize={30} className="flex flex-col relative pb-2">
                                    <div className="glass-panel p-4 rounded-lg flex-1 w-full relative">
                                        {chartData.length > 0 ? (
                                            <TradingChart data={chartData} />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center text-[var(--color-b-muted)]">
                                                Grafik verisi yükleniyor veya bulunamadı...
                                            </div>
                                        )}
                                    </div>
                                </Panel>

                                <PanelResizeHandle className="h-1.5 my-2 bg-gray-800 hover:bg-[var(--color-b-yellow)] rounded transition-colors cursor-row-resize flex justify-center items-center">
                                    <div className="w-8 h-0.5 bg-gray-500 rounded-full"></div>
                                </PanelResizeHandle>

                                <Panel defaultSize={40} minSize={20} className="flex flex-col space-y-6 overflow-y-auto pr-2 pb-4 pt-2">
                                    {/* AI Summary */}
                                    <div className="bg-[#1e2329] p-5 rounded-lg border-l-4 border-[var(--color-b-yellow)] flex-shrink-0">
                            <h3 className="font-bold text-white mb-2">🤖 Yapay Zeka Analiz Özeti</h3>
                            <p className="text-[var(--color-b-muted)] text-sm leading-relaxed whitespace-pre-wrap">
                                {data.ssot_result?.summary}
                            </p>
                        </div>

                        {/* Indicator Proof Table moved to Modal */}
                                </Panel>
                            </PanelGroup>
                        </Panel>
                    </PanelGroup>
                </div>
            )}
        </div>
        <AuthModal />
        
        {isIndicatorModalOpen && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setIsIndicatorModalOpen(false)}>
                <div 
                    className="bg-[#181a20] border border-[var(--color-b-border)] rounded-lg w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="flex justify-between items-center p-5 border-b border-[var(--color-b-border)]">
                        <div>
                            <h3 className="font-bold text-white text-xl">🔍 İndikatör Sinyal Detayları</h3>
                            <p className="text-[var(--color-b-muted)] text-sm mt-1">100+ teknik kuralın mevcut durumu ve hisseye etkisi</p>
                        </div>
                        <button onClick={() => setIsIndicatorModalOpen(false)} className="text-gray-400 hover:text-white text-2xl font-bold p-2">
                            &times;
                        </button>
                    </div>
                    <div className="overflow-y-auto w-full p-4">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-[#1e2329] text-[var(--color-b-muted)] sticky top-0 shadow-md">
                                <tr>
                                    <th className="p-3 font-semibold rounded-tl-md">İndikatör / Kural</th>
                                    <th className="p-3 font-semibold">Durum</th>
                                    <th className="p-3 font-semibold rounded-tr-md">Etki Ağırlığı</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data?.ssot_result?.core_votes_list?.map((vote: any, idx: number) => {
                                    const isAl = vote.Durum?.includes("AL");
                                    const isSat = vote.Durum?.includes("SAT");
                                    return (
                                        <tr key={idx} className="border-b border-[#2a3038] hover:bg-[#1e2329] transition-colors">
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
            </div>
        )}
        </>
    );
}

export default function AnalysisPage() {
    return (
        <Suspense fallback={<div className="p-8 text-white">Yükleniyor...</div>}>
            <AnalysisPageContent />
        </Suspense>
    );
}
