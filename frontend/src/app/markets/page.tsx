"use client";
import { useState, useEffect, useRef } from "react";
import TradingChart from "@/components/TradingChart";
import api from "@/lib/api";
import SymbolAutocomplete from "@/components/SymbolAutocomplete";

export default function Home() {
    const [chartData, setChartData] = useState([]);
    
    // Read initial ticker from URL if present (e.g. from Screener Incele button)
    const initialTicker = typeof window !== "undefined" 
        ? new URLSearchParams(window.location.search).get("ticker") || "XU100" 
        : "XU100";
        
    const [selectedTicker, setSelectedTicker] = useState(initialTicker);
    const [interval, setInterval] = useState("1d");
    const [loading, setLoading] = useState(true);
    
    // Watchlist state and prices
    const [watchlist, setWatchlist] = useState<string[]>([]);
    const [prices, setPrices] = useState<any>({});
    const [newTicker, setNewTicker] = useState("");
    const [showAddInput, setShowAddInput] = useState(false);

    // Calendar state
    const [calendar, setCalendar] = useState<any[]>([]);
    
    // Initial Load of Watchlist and Calendar
    useEffect(() => {
        const fetchWatchlist = async () => {
            try {
                const res = await api.get('/screener/watchlist');
                let wlFromDb = res.data.watchlist || [];
                
                // Gelen data obje listesiyse Ticker olarak dönüştür
                if (wlFromDb.length > 0 && typeof wlFromDb[0] === 'object') {
                    wlFromDb = wlFromDb.map((item: any) => item.Ticker || item.ticker);
                }

                // PORTFÖYDEKİ HİSSELERİ ÇEK VE İZLEME LİSTESİNE EKLE
                try {
                    const portRes = await api.get('/portfolio/');
                    if (portRes.data && portRes.data.data) {
                        const portTickers = portRes.data.data.map((p: any) => p.Hisse || p.ticker || p.Ticker);
                        portTickers.forEach((t: string) => {
                            if (t && !wlFromDb.includes(t)) {
                                wlFromDb.push(t);
                                // Ayrıca veritabanına da izleme listesi öğesi olarak ekle
                                api.post('/screener/watchlist', { ticker: t }).catch(() => {});
                            }
                        });
                    }
                } catch (portErr) {
                    console.error("Portföy çekerken hata:", portErr);
                }
                
                // SADECE DB'DEN GELENLERİ KULLAN, localstorage sadece db listesindeki elemanları sıralamak için kullanılsın
                // Başka bir userın localstorage'ı ile karışmasını engelliyoruz
                const savedOrder = localStorage.getItem('watchlistOrder');
                if (savedOrder && savedOrder !== "undefined") {
                    try {
                        const parsedOrder = JSON.parse(savedOrder);
                        // Db'den gelen listeyi, local storage'daki sıraya göre diz
                        wlFromDb.sort((a: string, b: string) => {
                            const idxA = parsedOrder.indexOf(a);
                            const idxB = parsedOrder.indexOf(b);
                            if (idxA === -1 && idxB === -1) return 0;
                            if (idxA === -1) return 1;
                            if (idxB === -1) return -1;
                            return idxA - idxB;
                        });
                    } catch(e) {
                        console.error("Localstorage parsing error", e);
                    }
                }

                
                // Eğer hala boşsa
                if (wlFromDb.length === 0) {
                    const defaultList = ["XU100", "XU030", "THYAO", "TUPRS", "KCHOL", "EREGL", "GARAN", "AKBNK", "ISCTR", "SAHOL", "ASELS"];
                    wlFromDb = defaultList;
                    Promise.all(defaultList.map(ticker => 
                        api.post('/screener/watchlist', { ticker }).catch(() => {})
                    ));
                }
                
                setWatchlist(wlFromDb);
            } catch (error) {
                console.error("Watchlist fetch error:", error);
                const savedOrder = localStorage.getItem('watchlistOrder');
                if (savedOrder && savedOrder !== "undefined") {
                    try {
                        setWatchlist(JSON.parse(savedOrder));
                    } catch(e) {
                        setWatchlist(["XU100", "XU030", "THYAO", "TUPRS", "KCHOL", "EREGL", "GARAN", "AKBNK", "ISCTR", "SAHOL", "ASELS"]); // Fallback
                    }
                } else {
                    setWatchlist(["XU100", "XU030", "THYAO", "TUPRS", "KCHOL", "EREGL", "GARAN", "AKBNK", "ISCTR", "SAHOL", "ASELS"]); // Fallback
                }
            }
        };
        fetchWatchlist();

        // Fetch Calendar
        api.get('/market/calendar').then(res => {
            if(res.data && res.data.data) {
                setCalendar(res.data.data);
            }
        }).catch(err => console.error("Calendar fetch error:", err));

    }, []);

    // Drag and Drop refs
    const dragItem = useRef<number | null>(null);
    const dragOverItem = useRef<number | null>(null);

    const handleSort = () => {
        if (dragItem.current !== null && dragOverItem.current !== null) {
            let _watchlist = [...watchlist];
            const draggedItemContent = _watchlist.splice(dragItem.current, 1)[0];
            _watchlist.splice(dragOverItem.current, 0, draggedItemContent);
            dragItem.current = null;
            dragOverItem.current = null;
            setWatchlist(_watchlist);
            localStorage.setItem('watchlistOrder', JSON.stringify(_watchlist));
        }
    };

    // Fetch Chart Data
    useEffect(() => {
        const fetchChartData = async () => {
            setLoading(true);
            let period = "1y";
            if (interval === "1h") period = "1mo";
            if (interval === "4h") period = "3mo";
            
            try {
                const res = await api.get(`/data/ohlcv/${selectedTicker}?interval=${interval}&period=${period}`);
                if (res.data && res.data.data) {
                    setChartData(res.data.data);
                }
            } catch (error) {
                console.error("Failed to fetch chart data:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchChartData();
    }, [selectedTicker, interval]);

    // Fetch Batch Prices for Watchlist
    useEffect(() => {
        if (watchlist.length === 0) return;
        
        const fetchPrices = async () => {
            try {
                const res = await api.post('/data/prices/batch', { tickers: watchlist });
                if (res.data && res.data.data) {
                    setPrices(res.data.data);
                }
            } catch (error) {
                console.error("Batch price fetch error:", error);
            }
        };
        fetchPrices();
        const intervalId = window.setInterval(fetchPrices, 60000); // 1 dakikada bir güncelle
        return () => window.clearInterval(intervalId);
    }, [watchlist]);

    const handleAddTicker = async (tickerToAdd: string) => {
        const upper = tickerToAdd.trim().toUpperCase();
        if (upper && !watchlist.includes(upper)) {
            // Optimistic update
            const newList = [upper, ...watchlist];
            setWatchlist(newList);
            localStorage.setItem('watchlistOrder', JSON.stringify(newList));
            
            try {
                const res = await api.post('/screener/watchlist', { ticker: upper });
                if (res.status !== 200) {
                    throw new Error("Backend error");
                }
            } catch(e) { 
                console.error("Ekleme hatası, geri alınıyor", e);
                // Revert
                setWatchlist(watchlist);
                localStorage.setItem('watchlistOrder', JSON.stringify(watchlist));
                alert("Hisse izleme listesine eklenemedi (Veritabanı hatası).");
            }
        }
        setNewTicker("");
        setShowAddInput(false);
    };

    const removeTicker = async (ticker: string, e: any) => {
        e.stopPropagation();
        const newList = watchlist.filter(t => t !== ticker);
        setWatchlist(newList);
        localStorage.setItem('watchlistOrder', JSON.stringify(newList));
        try {
            await api.delete(`/screener/watchlist/${ticker}`);
        } catch(e) { console.error("Silme hatası", e); }
    };

    // Current ticker info
    const currentPriceInfo = prices[selectedTicker];
    const priceColor = currentPriceInfo && currentPriceInfo.change >= 0 ? "text-[var(--color-b-green)]" : "text-[var(--color-b-red)]";
    const changePrefix = currentPriceInfo && currentPriceInfo.change > 0 ? "+" : "";

    return (
        <div className="flex w-full h-[calc(100vh-64px)] p-4 gap-4 bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-hidden">
            {/* Sidebar / Watchlist */}
            <aside className="w-80 glass-panel flex flex-col p-4 min-h-0">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="font-bold text-lg">Piyasa İzleme</h2>
                    <button 
                        onClick={() => setShowAddInput(!showAddInput)}
                        className="text-[var(--color-b-muted)] hover:text-[var(--color-b-yellow)] text-xl font-bold px-2"
                    >
                        +
                    </button>
                </div>
                
                {showAddInput && (
                    <div className="mb-4 flex gap-2">
                        <SymbolAutocomplete
                            value={newTicker}
                            onChange={(val) => setNewTicker(val)}
                            onSelect={(val) => handleAddTicker(val)}
                            placeholder="THYAO, FROTO..."
                            className="flex-1"
                        />
                        <button 
                            onClick={() => handleAddTicker(newTicker)}
                            disabled={!newTicker.trim()}
                            className="px-3 py-2 bg-[var(--color-b-yellow)] text-[#181a20] font-bold rounded hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Ekle
                        </button>
                    </div>
                )}
                
                <div className="flex flex-col gap-2 overflow-y-auto">
                    {watchlist.map((sym, index) => {
                        const info = prices[sym];
                        const isUp = info && info.change >= 0;
                        return (
                            <div 
                                key={sym} 
                                onClick={() => setSelectedTicker(sym)}
                                draggable
                                onDragStart={(e) => (dragItem.current = index)}
                                onDragEnter={(e) => (dragOverItem.current = index)}
                                onDragEnd={handleSort}
                                onDragOver={(e) => e.preventDefault()}
                                className={`flex justify-between items-center p-3 rounded bg-[var(--color-b-panel)] border cursor-move transition-colors group ${selectedTicker === sym ? "border-[var(--color-b-yellow)]" : "border-[var(--color-b-border)] hover:border-[var(--color-b-muted)]"}`}
                            >
                                <div className="flex flex-col">
                                    <div className="flex items-center gap-2">
                                        <span className={`font-bold transition-colors ${selectedTicker === sym ? "text-[var(--color-b-yellow)]" : "group-hover:text-white"}`}>{sym}</span>
                                        {sym !== "XU100" && sym !== "XU030" && (
                                            <button onClick={(e) => removeTicker(sym, e)} className="text-[var(--color-b-red)] opacity-0 group-hover:opacity-100 transition-opacity text-xs">x</button>
                                        )}
                                    </div>
                                    <span className="text-xs text-[var(--color-b-muted)]">BIST</span>
                                </div>
                                <div className="flex flex-col items-end pointer-events-none">
                                    <span className="font-medium text-white text-sm">
                                        {info ? (info.price !== 0 ? info.price.toFixed(2) : "Bulunamadı") : "--"}
                                    </span>
                                    <span className={`text-xs font-bold ${isUp ? "text-[var(--color-b-green)]" : "text-[var(--color-b-red)]"}`}>
                                        {info ? (info.change !== 0 ? `${info.change > 0 ? "+" : ""}${info.change.toFixed(2)}%` : "0.00%") : "--"}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </aside>

            {/* Main Content (Chart & Signals) */}
            <section className="flex-1 flex flex-col gap-4 min-h-0">
                {/* Upper Info Bar */}
                <div className="glass-panel p-4 flex items-center gap-8">
                    <div>
                        <h2 className="text-2xl font-bold text-white">{selectedTicker} <span className="text-sm font-normal text-[var(--color-b-muted)]">BIST Hissesi</span></h2>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-xs text-[var(--color-b-muted)] uppercase tracking-wider font-semibold mb-1">Anlık Fiyat</span>
                        <span className={`text-xl font-bold ${priceColor}`}>
                            {currentPriceInfo ? (currentPriceInfo.price !== 0 ? currentPriceInfo.price.toFixed(2) : "Veri Yok") : "Yükleniyor..."}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-xs text-[var(--color-b-muted)] uppercase tracking-wider font-semibold mb-1">Değişim (%)</span>
                        <span className={`text-md font-medium ${priceColor}`}>
                            {currentPriceInfo ? (currentPriceInfo.change !== 0 ? `${changePrefix}${currentPriceInfo.change.toFixed(2)}%` : "0.00%") : "--"}
                        </span>
                    </div>
                </div>

                {/* Chart Area */}
                <div className="glass-panel flex-1 p-1 relative overflow-hidden flex flex-col">
                    {/* Toolbar inside chart */}
                    <div className="flex items-center gap-4 px-4 py-2 border-b border-[var(--color-b-border)] bg-[rgba(11,14,17,0.5)]">
                        <span 
                            onClick={() => setInterval("1d")}
                            className={`text-sm cursor-pointer font-medium ${interval === "1d" ? "text-[var(--color-b-yellow)] border-b border-[var(--color-b-yellow)]" : "text-[var(--color-b-muted)] hover:text-white"}`}
                        >
                            1G
                        </span>
                        <span 
                            onClick={() => setInterval("4h")}
                            className={`text-sm cursor-pointer font-medium ${interval === "4h" ? "text-[var(--color-b-yellow)] border-b border-[var(--color-b-yellow)]" : "text-[var(--color-b-muted)] hover:text-white"}`}
                        >
                            4S
                        </span>
                        <span 
                            onClick={() => setInterval("1h")}
                            className={`text-sm cursor-pointer font-medium ${interval === "1h" ? "text-[var(--color-b-yellow)] border-b border-[var(--color-b-yellow)]" : "text-[var(--color-b-muted)] hover:text-white"}`}
                        >
                            1S
                        </span>
                        <div className="w-[1px] h-4 bg-[var(--color-b-border)] mx-2"></div>
                        <span className="text-sm text-[var(--color-b-green)] font-medium">İndikatörler Aktif (SMA20, EMA50) 📈</span>
                    </div>
                    <div className="flex-1 w-full relative">
                        {loading ? (
                            <div className="absolute inset-0 flex items-center justify-center text-[var(--color-b-muted)]">
                                Grafik Verileri Yükleniyor...
                            </div>
                        ) : chartData.length > 0 ? (
                            <TradingChart data={chartData} />
                        ) : (
                            <div className="absolute inset-0 flex items-center justify-center text-[var(--color-b-muted)]">
                                {selectedTicker} için veri bulunamadı.
                            </div>
                        )}
                    </div>
                </div>

                {/* Macro Calendar Widget */}
                <div className="glass-panel h-48 flex flex-col overflow-hidden">
                    <div className="p-3 border-b border-[var(--color-b-border)] flex items-center justify-between bg-[#1e2329]">
                        <h3 className="font-bold text-white text-sm">📅 Makroekonomik Takvim</h3>
                        <span className="text-xs text-[var(--color-b-muted)]">TCMB & FED & Enflasyon</span>
                    </div>
                    <div className="flex-1 overflow-auto p-0">
                        <table className="w-full text-left text-sm border-collapse">
                            <thead className="bg-[#181a20] text-[var(--color-b-muted)] text-xs sticky top-0">
                                <tr>
                                    <th className="p-2 border-b border-[var(--color-b-border)] font-semibold">Tarih</th>
                                    <th className="p-2 border-b border-[var(--color-b-border)] font-semibold">Saat</th>
                                    <th className="p-2 border-b border-[var(--color-b-border)] font-semibold">Ülke</th>
                                    <th className="p-2 border-b border-[var(--color-b-border)] font-semibold">Olay</th>
                                    <th className="p-2 border-b border-[var(--color-b-border)] font-semibold">Beklenti</th>
                                    <th className="p-2 border-b border-[var(--color-b-border)] font-semibold">Önceki</th>
                                </tr>
                            </thead>
                            <tbody>
                                {calendar.length === 0 ? (
                                    <tr><td colSpan={6} className="p-4 text-center text-[var(--color-b-muted)]">Veri Bekleniyor...</td></tr>
                                ) : (
                                    calendar.map((ev, i) => (
                                        <tr key={i} className="hover:bg-[#1e2329] border-b border-[var(--color-b-border)] transition-colors">
                                            <td className="p-2 text-white">{ev.date}</td>
                                            <td className="p-2 text-[var(--color-b-muted)]">{ev.time}</td>
                                            <td className="p-2 text-white font-bold">{ev.country === 'TR' ? '🇹🇷' : '🇺🇸'}</td>
                                            <td className="p-2 text-[var(--color-b-yellow)] font-medium">{ev.event}</td>
                                            <td className="p-2 text-white">{ev.forecast}</td>
                                            <td className="p-2 text-[var(--color-b-muted)]">{ev.previous}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

            </section>
        </div>
    );
}
