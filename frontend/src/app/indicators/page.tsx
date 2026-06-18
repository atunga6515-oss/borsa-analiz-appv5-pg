"use client";

import React, { useEffect, useState } from "react";
import LayeredChart, { LayerKeys } from "@/components/LayeredChart";
import api from "@/lib/api";
import { toast } from "react-hot-toast";
import { getWatchlist, addTickerToWatchlist, removeTickerFromWatchlist } from "@/lib/watchlist";

export default function IndicatorsDashboard() {
    const [watchlist, setWatchlist] = useState<string[]>([]);
    const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
    const [chartData, setChartData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [manualInput, setManualInput] = useState("");
    const [aiLoading, setAiLoading] = useState<boolean>(false);
    const [aiResult, setAiResult] = useState<{ decision: string; summary: string } | null>(null);
    const [activeLayers, setActiveLayers] = useState<Record<LayerKeys, boolean>>({
        autoTrend: false, supertrend: false, alphaSignal: false, smcFvg: false, squeeze: false, wavetrend: false,
        divergence: false, anchoredVwap: false, volProfilePoc: false, chandelier: false, adxDmi: false, stochRSI: false, cmf: false, donchian: false, ichimoku: false, bollinger: false
    });
    const [aiHistory, setAiHistory] = useState<any[]>([]);
    const [showPreModal, setShowPreModal] = useState(false);
    const [showResultModal, setShowResultModal] = useState(false);
    const [showHistoryDropdown, setShowHistoryDropdown] = useState(false);

    // Load watchlist from utility
    const loadWatchlist = () => {
        const parsed = getWatchlist();
        setWatchlist(parsed);
        if (parsed.length > 0 && !selectedTicker) {
            setSelectedTicker(parsed[0]);
        } else if (parsed.length === 0) {
            setSelectedTicker(null);
            setChartData(null);
        }
    };

    useEffect(() => {
        loadWatchlist();
        // Listen for storage events (if changed from other tabs)
        window.addEventListener("storage", loadWatchlist);
        // Custom event for same-tab updates
        window.addEventListener("watchlist_updated", loadWatchlist);
        // Load AI History
        try {
            const savedHistory = localStorage.getItem('alfabist_ai_history');
            if (savedHistory) setAiHistory(JSON.parse(savedHistory));
        } catch (e) {
            console.error("Error loading aiHistory from localStorage");
        }

        return () => {
            window.removeEventListener("storage", loadWatchlist);
            window.removeEventListener("watchlist_updated", loadWatchlist);
        };
    }, []);

    // Fetch data when ticker changes
    useEffect(() => {
        if (!selectedTicker) {
            setChartData(null);
            setAiResult(null);
            return;
        }

        setAiResult(null);
        setActiveLayers({
            autoTrend: false, supertrend: false, alphaSignal: false, smcFvg: false, squeeze: false, wavetrend: false,
            divergence: false, anchoredVwap: false, volProfilePoc: false, chandelier: false, adxDmi: false, stochRSI: false, cmf: false, donchian: false, ichimoku: false, bollinger: false
        });

        let isMounted = true;
        setLoading(true);

        api.get(`/analysis/layered-data?ticker=${selectedTicker}`)
            .then((res) => {
                if (isMounted && res.data) {
                    setChartData(res.data);
                }
            })
            .catch((err) => {
                console.error(err);
                if (isMounted) toast.error(`${selectedTicker} verisi alınamadı.`);
            })
            .finally(() => {
                if (isMounted) setLoading(false);
            });

        return () => {
            isMounted = false;
        };
    }, [selectedTicker]);



    const handleRemoveFromWatchlist = (e: React.MouseEvent, ticker: string) => {
        e.stopPropagation();
        removeTickerFromWatchlist(ticker);
    };

    const handleManualAdd = (e: React.FormEvent) => {
        e.preventDefault();
        if (manualInput.trim()) {
            addTickerToWatchlist(manualInput);
            setManualInput("");
        }
    };

    const handleAIAnalysis = async () => {
        if (!selectedTicker) return;
        setAiLoading(true);
        setAiResult(null);
        setShowPreModal(false);
        try {
            const activeIndicatorKeys = Object.entries(activeLayers).filter(([k, v]) => v).map(([k]) => k);
            const res = await api.post('/ai/analyze-indicators', { ticker: selectedTicker, active_indicators: activeIndicatorKeys });
            if (res.data) {
                setAiResult(res.data);
                setShowResultModal(true);
            }
        } catch (err) {
            console.error("AI Analysis failed:", err);
            toast.error("Yapay Zeka analizi sırasında bir hata oluştu.");
        } finally {
            setAiLoading(false);
        }
    };

    const handleSaveAnalysis = () => {
        if (!aiResult || !selectedTicker) return;
        const newEntry = { ticker: selectedTicker, date: new Date().toLocaleString(), ...aiResult };
        const newHistory = [newEntry, ...aiHistory].slice(0, 10);
        setAiHistory(newHistory);
        localStorage.setItem('alfabist_ai_history', JSON.stringify(newHistory));
        toast.success("Analiz kaydedildi!");
        setShowResultModal(false);
    };

    const handleToggleLayer = (key: LayerKeys) => {
        setActiveLayers(prev => ({ ...prev, [key]: !prev[key] }));
    };

    return (
        <div className="flex w-full h-[calc(100vh-64px)] bg-gray-900 text-white overflow-hidden">
            {/* Left Sidebar: Watchlist */}
            <div className="w-64 border-r border-gray-800 bg-gray-900/50 flex flex-col">
                <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                    <h2 className="text-sm font-semibold tracking-wider text-gray-400 uppercase">İzleme Listem</h2>
                    <span className="text-xs bg-gray-800 px-2 py-1 rounded-full">{watchlist.length}/10</span>
                </div>

                <div className="p-3 border-b border-gray-800">
                    <form onSubmit={handleManualAdd} className="flex gap-2">
                        <input 
                            type="text" 
                            value={manualInput} 
                            onChange={(e) => setManualInput(e.target.value)}
                            placeholder="THYAO.IS" 
                            className="w-full bg-gray-800 text-white px-3 py-1.5 rounded border border-gray-700 text-sm focus:outline-none focus:border-blue-500 uppercase"
                        />
                        <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded text-sm font-bold transition-colors">
                            +
                        </button>
                    </form>
                </div>
                
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {watchlist.length === 0 ? (
                        <div className="text-center p-4 text-gray-500 text-sm mt-10">
                            Listeniz boş.<br/><br/>AlphaRank, Screener veya diğer listelerden hisselerin yanındaki <b className="text-gray-400">+</b> butonuna basarak buraya ekleyebilirsiniz.
                        </div>
                    ) : (
                        watchlist.map(ticker => (
                            <div 
                                key={ticker}
                                onClick={() => setSelectedTicker(ticker)}
                                className={`flex items-center justify-between px-4 py-3 rounded-lg cursor-pointer transition-all ${selectedTicker === ticker ? 'bg-blue-600/20 border border-blue-500/50' : 'hover:bg-gray-800 border border-transparent'}`}
                            >
                                <span className={`font-semibold ${selectedTicker === ticker ? 'text-blue-400' : 'text-gray-200'}`}>{ticker.replace('.IS', '')}</span>
                                <button 
                                    onClick={(e) => handleRemoveFromWatchlist(e, ticker)}
                                    className="text-gray-500 hover:text-red-400 p-1"
                                    title="Listeden Çıkar"
                                >
                                    ✕
                                </button>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Right Main Area: Chart & Controls */}
            <div className="flex-1 flex flex-col relative">
                {/* Top Controls */}
                <div className="h-16 border-b border-gray-800 flex items-center px-6 gap-6 bg-gray-900/80 backdrop-blur-sm z-10 shrink-0">
                    <div className="flex items-center gap-4 border-r border-gray-700 pr-6 mr-2">
                        <span className="text-xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500 tracking-tight">
                            PRO TERMINAL
                        </span>
                    </div>
                    <div className="text-2xl font-bold text-white flex items-center gap-4">
                        <span>{selectedTicker ? selectedTicker.replace('.IS', '') : "Seçim Yok"}</span>
                        {chartData && chartData.quote && (
                            <div className="flex items-center gap-2 text-base font-medium bg-[#2b3139] px-3 py-1 rounded">
                                <span className="text-gray-200">{chartData.quote.price.toFixed(2)}</span>
                                <span className={chartData.quote.change_pct >= 0 ? "text-green-400" : "text-red-400"}>
                                    {chartData.quote.change_pct >= 0 ? "+" : ""}{chartData.quote.change_pct.toFixed(2)}%
                                </span>
                            </div>
                        )}
                    </div>
                    {/* Right side of top bar */}
                    {chartData && (
                        <div className="ml-auto flex items-center gap-3 relative">
                            <button 
                                onClick={() => setShowHistoryDropdown(!showHistoryDropdown)}
                                className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded border border-gray-700 transition-colors flex items-center gap-2"
                            >
                                Geçmiş Yapay Zeka Analiz Sonuçları ▾
                            </button>
                            {showHistoryDropdown && (
                                <div className="absolute top-10 right-32 w-64 bg-gray-800 border border-gray-700 rounded shadow-xl z-50">
                                    <div className="p-2 text-xs text-gray-400 border-b border-gray-700 font-bold uppercase tracking-wider">Son Analizler</div>
                                    <div className="max-h-60 overflow-y-auto">
                                        {aiHistory.length === 0 ? (
                                            <div className="p-3 text-sm text-gray-500 italic">Kayıt yok</div>
                                        ) : (
                                            aiHistory.map((entry, idx) => (
                                                <div key={idx} onClick={() => { setAiResult(entry); setShowResultModal(true); setShowHistoryDropdown(false); }} className="p-3 border-b border-gray-700 hover:bg-gray-700 cursor-pointer">
                                                    <div className="flex justify-between items-center mb-1">
                                                        <span className="font-bold text-white">{entry.ticker}</span>
                                                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${entry.decision.includes('BUY') ? 'bg-emerald-900 text-emerald-400' : entry.decision.includes('SELL') ? 'bg-rose-900 text-rose-400' : 'bg-gray-700 text-gray-300'}`}>{entry.decision}</span>
                                                    </div>
                                                    <div className="text-[10px] text-gray-400">{entry.date}</div>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}
                            
                            <button 
                                onClick={() => setShowPreModal(true)}
                                className="px-6 py-2 bg-gradient-to-r from-purple-700 to-indigo-600 hover:from-purple-600 hover:to-indigo-500 text-white font-black rounded-lg shadow-[0_0_15px_rgba(147,51,234,0.4)] text-sm transition-all border border-purple-400 flex items-center gap-2 tracking-wide"
                            >
                                🤖 YAPAY ZEKA İLE ANALİZ ET
                            </button>
                        </div>
                    )}
                </div>

                {/* Chart Area */}
                <div className="flex-1 p-4 overflow-y-auto">
                    <div className="w-full bg-[#1A1D24] rounded-xl border border-gray-800 shadow-xl overflow-hidden relative" style={{ minHeight: '600px' }}>
                        {!selectedTicker ? (
                            <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                                Soldaki menüden bir hisse seçin.
                            </div>
                        ) : loading ? (
                            <div className="absolute inset-0 flex items-center justify-center text-blue-400">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mr-3"></div>
                                Grafikler Yükleniyor...
                            </div>
                        ) : chartData ? (
                            <LayeredChart data={chartData} activeLayers={activeLayers} onToggleLayer={handleToggleLayer} />
                        ) : null}
                    </div>
                </div>
            </div>


            {/* Pre-Analysis Modal */}
            {showPreModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="bg-[#1e2329] border border-gray-700 rounded-xl shadow-2xl p-6 w-[450px] flex flex-col gap-4">
                        <h3 className="text-lg font-bold text-yellow-500 flex items-center gap-2">🤖 Yapay Zeka Analizi Başlatılıyor</h3>
                        <p className="text-sm text-gray-300 leading-relaxed">
                            Analiz, şu an grafikte aktif olan aşağıdaki indikatörlerin matematiksel kesişimleri kullanılarak yapılacaktır:
                        </p>
                        <div className="bg-gray-800 p-3 rounded text-sm text-blue-300 font-mono">
                            {Object.entries(activeLayers).filter(([k,v]) => v).length > 0 
                                ? Object.entries(activeLayers).filter(([k,v]) => v).map(([k]) => k).join(", ") 
                                : "Sadece fiyat ve hacim (İndikatör seçilmedi)"}
                        </div>
                        <p className="text-xs text-gray-500 italic">
                            İsterseniz iptal edip grafikteki indikatör sayısını azaltabilir veya arttırabilirsiniz. Bu işlem kotanızı etkiler.
                        </p>
                        
                        <div className="flex gap-3 justify-end mt-2">
                            <button onClick={() => setShowPreModal(false)} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-semibold transition-colors">İptal</button>
                            <button onClick={handleAIAnalysis} disabled={aiLoading} className="px-4 py-2 bg-purple-700 hover:bg-purple-600 text-white rounded text-sm font-semibold transition-colors flex items-center gap-2">
                                {aiLoading ? <span className="animate-spin">⏳</span> : "✨"} Analizi Başlat
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Result Modal */}
            {showResultModal && aiResult && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="bg-[#1e2329] border border-gray-700 rounded-xl shadow-2xl p-8 w-[650px] flex flex-col gap-5">
                        <div className="flex justify-between items-center border-b border-gray-800 pb-4">
                            <h3 className="text-base font-bold text-yellow-500 uppercase tracking-wider flex items-center gap-2">
                                🤖 Kantitatif Karar Matrisi (0-15 Gün)
                            </h3>
                            <span className={`px-4 py-1.5 rounded text-sm font-black tracking-widest ${
                                aiResult.decision.includes('BUY') ? 'bg-emerald-950 text-emerald-400 border border-emerald-500' :
                                aiResult.decision.includes('SELL') ? 'bg-rose-950 text-rose-400 border border-rose-500' : 'bg-gray-800 text-gray-300 border border-gray-600'
                            }`}>
                                {aiResult.decision}
                            </span>
                        </div>
                        
                        <p className="text-lg text-gray-200 leading-relaxed italic">
                            "{aiResult.summary}"
                        </p>

                        <div className="flex gap-3 justify-end mt-4 border-t border-gray-800 pt-5">
                            <button onClick={() => setShowResultModal(false)} className="px-5 py-2.5 bg-gray-700 hover:bg-gray-600 rounded text-sm font-semibold transition-colors">Kapat</button>
                            <button onClick={handleSaveAnalysis} className="px-5 py-2.5 bg-blue-700 hover:bg-blue-600 text-white rounded text-sm font-semibold transition-colors">💾 Sonucu Kaydet</button>
                        </div>
                    </div>
                </div>
            )}

            {/* AI Loading Overlay */}
            {aiLoading && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
                    <div className="bg-[#1e2329] border border-gray-700 rounded-xl shadow-2xl p-8 flex flex-col items-center gap-5">
                        <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
                        <p className="text-lg text-gray-300 font-medium">Yapay Zeka grafiği okuyor, lütfen bekleyin...</p>
                    </div>
                </div>
            )}
        </div>
    );
}
