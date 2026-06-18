"use client";

import React, { useEffect, useState } from "react";
import LayeredChart from "@/components/LayeredChart";
import api from "@/lib/api";
import { toast } from "react-hot-toast";
import { getWatchlist, addTickerToWatchlist, removeTickerFromWatchlist } from "@/lib/watchlist";

export default function IndicatorsDashboard() {
    const [watchlist, setWatchlist] = useState<string[]>([]);
    const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
    const [chartData, setChartData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [manualInput, setManualInput] = useState("");

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
        return () => {
            window.removeEventListener("storage", loadWatchlist);
            window.removeEventListener("watchlist_updated", loadWatchlist);
        };
    }, []);

    // Fetch data when ticker changes
    useEffect(() => {
        if (!selectedTicker) {
            setChartData(null);
            return;
        }

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
                            <LayeredChart data={chartData} />
                        ) : null}
                    </div>
                </div>
            </div>
        </div>
    );
}
