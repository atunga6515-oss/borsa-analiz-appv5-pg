"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import SMCChart from "@/components/SMCChart";
import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function SMCPage() {
    const { requireAuth, AuthModal } = useRequireAuth();
    const [ticker, setTicker] = useState("THYAO");
    const [inputTicker, setInputTicker] = useState("THYAO");
    const [loading, setLoading] = useState(false);
    
    const [chartData, setChartData] = useState<any[]>([]);
    const [marketStructure, setMarketStructure] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async (symbol: string) => {
        if (!symbol) return;
        setLoading(true);
        setError(null);
        try {
            // 1. Fetch Deep Analysis for Market Structure
            const deepRes = await api.get(`/analysis/deep?ticker=${symbol.toUpperCase()}`);
            if (deepRes.data && deepRes.data.data) {
                setMarketStructure(deepRes.data.data.market_structure);
            }

            // 2. Fetch Chart Data
            const chartRes = await api.get(`/analysis/chart?ticker=${symbol.toUpperCase()}`);
            if (chartRes.data && chartRes.data.data) {
                setChartData(chartRes.data.data);
            } else {
                setChartData([]);
            }
        } catch (err: any) {
            console.error("SMC Data Fetch Error", err);
            setError(err.response?.data?.detail || "Veriler alınırken bir hata oluştu.");
            setMarketStructure(null);
            setChartData([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData(ticker);
    }, [ticker]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setTicker(inputTicker.toUpperCase());
    };

    return (
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="flex justify-between items-end mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">📐 SMC Terminali</h1>
                    <p className="text-[var(--color-b-muted)] mb-4">Smart Money Concepts (Akıllı Para Konseptleri) ile Market Yapısı Kırılımlarını (BOS) İnceleyin</p>
                    
                    <div className="bg-purple-900/20 border border-purple-500/30 p-3 rounded text-sm text-purple-200 max-w-4xl">
                        <strong>ℹ️ SMC Mantığı:</strong> Fiyat hareketlerindeki arz ve talep bölgelerini izler. Zirve seviyesi yukarı yönlü geçildiğinde (BOS - Break of Structure), yükseliş trendi teyit edilir. 
                    </div>
                </div>
            </div>

            <div className="flex gap-4 mb-6">
                <form onSubmit={handleSearch} className="flex gap-2 w-full max-w-sm">
                    <input 
                        type="text" 
                        value={inputTicker} 
                        onChange={(e) => setInputTicker(e.target.value.toUpperCase())}
                        placeholder="Hisse Kodu (Örn: THYAO)"
                        className="flex-1 bg-[#1e2329] border border-[var(--color-b-border)] rounded px-4 py-2 text-white focus:outline-none focus:border-[var(--color-b-yellow)]"
                    />
                    <button 
                        type="submit"
                        className="bg-[var(--color-b-yellow)] text-black px-6 py-2 rounded font-bold hover:bg-yellow-500 transition-colors"
                    >
                        Analiz Et
                    </button>
                </form>
            </div>

            {loading ? (
                <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-b-yellow)]">
                    <div className="text-5xl mb-4 animate-spin">⏳</div>
                    <p>SMC verileri hesaplanıyor...</p>
                </div>
            ) : error ? (
                <div className="flex-1 flex items-center justify-center text-red-400">
                    <div className="bg-red-900/20 border border-red-500/30 p-6 rounded text-center">
                        <div className="text-4xl mb-4">❌</div>
                        <p>{error}</p>
                    </div>
                </div>
            ) : (
                <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-[500px]">
                    <div className="glass-panel p-4 rounded-lg flex-1 min-w-[60%] flex flex-col">
                        <h2 className="text-lg font-bold text-white mb-4">{ticker} - SMC Grafiği</h2>
                        <div className="flex-1 min-h-[400px]">
                            {chartData.length > 0 ? (
                                <SMCChart 
                                    data={chartData} 
                                    lastPeak={marketStructure?.last_peak} 
                                    lastTrough={marketStructure?.last_trough} 
                                />
                            ) : (
                                <div className="h-full flex items-center justify-center text-[var(--color-b-muted)]">
                                    Grafik verisi bulunamadı.
                                </div>
                            )}
                        </div>
                    </div>
                    
                    <div className="flex flex-col gap-4 w-full lg:w-[400px]">
                        <div className="bg-[#181a20] p-5 rounded-lg border border-[var(--color-b-border)] h-full">
                            <h3 className="font-bold text-white mb-4 text-xl">Market Yapısı Analizi</h3>
                            
                            <div className="space-y-6">
                                <div className="p-4 bg-[#1e2329] rounded-lg border border-gray-800">
                                    <div className="text-sm text-gray-400 mb-1">Durum (BOS)</div>
                                    <div className={`text-2xl font-bold ${marketStructure?.bos_detected ? "text-[var(--color-b-yellow)]" : "text-gray-500"}`}>
                                        {marketStructure?.bos_detected ? "KIRILIM GERÇEKLEŞTİ 🔥" : "KIRILIM YOK"}
                                    </div>
                                    <p className="text-xs text-gray-400 mt-2">
                                        {marketStructure?.bos_detected 
                                            ? "Son zirve noktası hacimli bir şekilde yukarı yönlü kırıldı. Yükseliş trendinin teyit edildiği anlamına gelir." 
                                            : "Henüz bir market yapısı kırılımı gözlemlenmedi. Konsolidasyon veya düşüş süreci devam ediyor olabilir."}
                                    </p>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 bg-[#1e2329] rounded-lg border border-gray-800">
                                        <div className="text-sm text-gray-400 mb-1">Lokal Zirve (Direnç)</div>
                                        <div className="text-xl font-bold text-red-400">
                                            {marketStructure?.last_peak ? marketStructure.last_peak.toFixed(2) + " ₺" : "-"}
                                        </div>
                                    </div>
                                    <div className="p-4 bg-[#1e2329] rounded-lg border border-gray-800">
                                        <div className="text-sm text-gray-400 mb-1">Lokal Dip (Destek)</div>
                                        <div className="text-xl font-bold text-green-400">
                                            {marketStructure?.last_trough ? marketStructure.last_trough.toFixed(2) + " ₺" : "-"}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            <AuthModal />
        </div>
    );
}
