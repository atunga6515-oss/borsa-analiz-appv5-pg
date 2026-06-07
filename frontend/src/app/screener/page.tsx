"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import AIAnalyzeModal from "../components/AIAnalyzeModal";

export default function ScreenerPage() {
    const router = useRouter();
    const { requireAuth, AuthModal } = useRequireAuth();
    const [scanResults, setScanResults] = useState<any[]>([]);
    const [scanning, setScanning] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);
    const [scanText, setScanText] = useState("");
    const [scanMode, setScanMode] = useState("BIST30");
    const [sortConfig, setSortConfig] = useState<{key: string | null, direction: 'asc' | 'desc'}>({ key: null, direction: 'asc' });
    
    // History State
    const [historyList, setHistoryList] = useState<any[]>([]);
    const [selectedHistoryId, setSelectedHistoryId] = useState<string>("");
    
    // AI Modal State
    const [aiModalOpen, setAiModalOpen] = useState(false);
    const [aiProps, setAiProps] = useState<any>({ ticker: "", price: 0 });
    
    
    // Portfolio Modal State
    const [modalOpen, setModalOpen] = useState(false);
    const [modalTicker, setModalTicker] = useState("");
    const [modalPrice, setModalPrice] = useState("");
    const [modalQty, setModalQty] = useState("100");
    
    const fetchHistoryList = async () => {
        try {
            const res = await api.get('/screener/history');
            if (res.data && res.data.data) {
                setHistoryList(res.data.data);
            }
        } catch(e) {
            console.error("Geçmiş çekilemedi", e);
        }
    };
    
    // İlk yüklemede history'yi çek (cookie-based auth, interceptor 401 yönetir)
    useEffect(() => {
        fetchHistoryList();
    }, []);
    
    const loadHistoryDetails = async (id: string) => {
        if (!id) return;
        setScanning(true);
        setScanText("Geçmiş sonuçlar yükleniyor...");
        try {
            const res = await api.get(`/screener/history/${id}`);
            if (res.data && res.data.data) {
                setScanResults(res.data.data);
            } else {
                setScanResults([]);
            }
        } catch(e) {
            console.error("Detay hatası:", e);
        } finally {
            setScanning(false);
        }
    };
    
    const runScan = async () => {
        setScanning(true);
        setScanProgress(0);
        setScanText("Sıraya alınıyor...");
        setScanResults([]); // Clear previous results while scanning
        try {
            const res = await api.post('/screener/scan', {
                scan_mode: scanMode
            });
            
            if (res.data && res.data.task_id) {
                const tid = res.data.task_id;
                
                const intervalId = setInterval(async () => {
                    try {
                        const statusRes = await api.get(`/screener/scan/progress/${tid}`);
                        const sData = statusRes.data;
                        
                        if (sData.status === "completed") {
                            clearInterval(intervalId);
                            setScanResults(sData.data || []);
                            setScanning(false);
                            setScanProgress(100);
                            fetchHistoryList(); // Taramadan sonra listeyi yenile
                        } else if (sData.status === "error") {
                            clearInterval(intervalId);
                            console.error("Tarama hatası:", sData.text);
                            setScanning(false);
                            alert("Tarama sırasında bir hata oluştu: " + sData.text);
                        } else if (sData.status === "not_found") {
                            clearInterval(intervalId);
                            setScanning(false);
                        } else {
                            setScanProgress(sData.progress || 0);
                            setScanText(sData.text || "");
                        }
                    } catch (err) {
                        console.error("Progress check error", err);
                    }
                }, 1000);
            } else if (res.data && res.data.data) {
                // Fallback for immediate response (if old backend happens)
                setScanResults(res.data.data);
                setScanning(false);
            }
        } catch (error) {
            console.error("Tarama hatası:", error);
            setScanning(false);
        }
    };

    const requestSort = (key: string) => {
        let direction: 'asc' | 'desc' = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const getSortIndicator = (key: string) => {
        if (sortConfig.key !== key) return <span className="opacity-30 ml-1">↕</span>;
        return sortConfig.direction === 'asc' ? <span className="text-[var(--color-b-yellow)] ml-1">▲</span> : <span className="text-[var(--color-b-yellow)] ml-1">▼</span>;
    };

    const sortedResults = [...scanResults].sort((a, b) => {
        if (sortConfig.key === null) return 0;
        
        const aVal = a[sortConfig.key] || "";
        const bVal = b[sortConfig.key] || "";
        
        // Handle numeric sorting
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return sortConfig.direction === 'asc' ? aNum - bNum : bNum - aNum;
        }

        // Handle string sorting
        const aStr = aVal.toString().toLowerCase();
        const bStr = bVal.toString().toLowerCase();
        if (aStr < bStr) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aStr > bStr) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

    const openModal = (ticker: string, price: string) => {
        requireAuth(() => {
            setModalTicker(ticker);
            setModalPrice(price !== "-" ? parseFloat(price).toFixed(2) : "");
            setModalQty("100");
            setModalOpen(true);
        });
    };

    const handlePortfolioAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.post('/portfolio/transaction', {
                ticker: modalTicker,
                type: 'ALIS',
                quantity: parseFloat(modalQty),
                price: parseFloat(modalPrice)
            });
            setModalOpen(false);
            alert(`${modalTicker} sanal portföye eklendi!`);
        } catch(error) {
            console.error("Portföy ekleme hatası:", error);
            alert("Portföye eklenirken hata oluştu.");
        }
    };
    
    const handleAIAnalysis = (row: any) => {
        setAiProps({
            ticker: row["Hisse"],
            price: parseFloat(row["Fiyat"] || 0),
            rsi: parseFloat(row["RSI"] || 0),
            macd_signal: row["MACD_Signal"],
            trend: row["Trend_Durumu"] || row["Piyasa Kararı"]
        });
        setAiModalOpen(true);
    };

    return (
        <>
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="flex justify-between items-end mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">⚡ Al-Sat Screener</h1>
                    <p className="text-[var(--color-b-muted)]">100 İndikatörlü Gelişmiş Algoritma ile BIST Taraması</p>
                    
                    {scanning && (
                        <div className="mt-4 flex items-center gap-3 bg-[var(--color-b-card)] p-3 rounded-lg border border-gray-800 shadow-md max-w-lg">
                            <div className="text-[var(--color-b-yellow)] animate-spin">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            </div>
                            <div className="flex-1 min-w-[250px]">
                                <div className="text-sm font-medium mb-1.5 text-white">{scanText || "Tarama başlatılıyor..."}</div>
                                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                    <div 
                                        className="h-full bg-[var(--color-b-yellow)] transition-all duration-300 ease-out"
                                        style={{ width: `${scanProgress}%` }}
                                    ></div>
                                </div>
                            </div>
                            <div className="text-sm font-bold text-[var(--color-b-yellow)] ml-2">{Math.round(scanProgress)}%</div>
                        </div>
                    )}
                    
                    <div className="flex gap-4 mt-4 items-center flex-wrap">
                        {["BIST30", "BIST100", "BIST_ALL"].map(mode => (
                            <label key={mode} className="flex items-center gap-2 cursor-pointer text-sm">
                                <input 
                                    type="radio" 
                                    name="scanMode" 
                                    value={mode} 
                                    checked={scanMode === mode}
                                    onChange={() => setScanMode(mode)}
                                    className="accent-[var(--color-b-yellow)]"
                                    disabled={scanning}
                                />
                                {mode === "BIST30" ? "BIST 30 (Hızlı)" : mode === "BIST100" ? "BIST 100" : "Tüm Hisseler"}
                            </label>
                        ))}
                        
                        {/* Geçmiş Dropdown */}
                        {historyList.length > 0 && (
                            <div className="ml-auto flex items-center gap-2">
                                <span className="text-sm text-gray-400">Son 30 Tarama:</span>
                                <select 
                                    className="bg-[var(--color-b-card)] border border-gray-700 text-white text-sm rounded px-3 py-1.5 focus:outline-none focus:border-[var(--color-b-yellow)]"
                                    value={selectedHistoryId}
                                    onChange={(e) => {
                                        const val = e.target.value;
                                        setSelectedHistoryId(val);
                                        if (val) loadHistoryDetails(val);
                                    }}
                                >
                                    <option value="">Seçiniz...</option>
                                    {historyList.map(h => (
                                        <option key={h.id} value={h.id}>
                                            {h.run_date}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}
                    </div>
                </div>
                <button 
                    onClick={() => requireAuth(runScan)} 
                    disabled={scanning}
                    className="px-6 py-3 bg-[var(--color-b-yellow)] text-black font-bold rounded hover:bg-yellow-500 transition-colors disabled:opacity-50 min-w-[200px]"
                >
                    {scanning ? "Tarama Yapılıyor..." : "Taramayı Başlat"}
                </button>
            </div>

            {/* Progress Bar Area */}
            <div className="w-full h-2 bg-[#1e2329] rounded overflow-hidden mb-4 relative">
                {scanning && (
                    <div className="absolute top-0 left-0 h-full bg-[var(--color-b-yellow)] animate-pulse w-full"
                         style={{
                             backgroundImage: 'linear-gradient(90deg, rgba(252,213,53,0.1) 0%, rgba(252,213,53,1) 50%, rgba(252,213,53,0.1) 100%)',
                             backgroundSize: '200% 100%',
                             animation: 'progress-bar-stripes 1.5s linear infinite'
                         }}
                    ></div>
                )}
                {/* CSS animation definition directly in the component for the stripes effect */}
                <style dangerouslySetInnerHTML={{__html: `
                    @keyframes progress-bar-stripes {
                        from { background-position: 200% 0; }
                        to { background-position: -200% 0; }
                    }
                `}} />
            </div>
            
            <div className="glass-panel flex-1 overflow-auto rounded-lg">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-[#1e2329] text-[var(--color-b-muted)] text-sm sticky top-0 z-10 shadow-md">
                        <tr>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold cursor-pointer hover:text-white select-none transition-colors" onClick={() => requestSort('Hisse')}>
                                Hisse {getSortIndicator('Hisse')}
                            </th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold cursor-pointer hover:text-white select-none transition-colors" onClick={() => requestSort('Piyasa Kararı')}>
                                Sinyal {getSortIndicator('Piyasa Kararı')}
                            </th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold cursor-pointer hover:text-white select-none transition-colors" onClick={() => requestSort('Ensemble Güven Skoru')}>
                                Trend & Skor {getSortIndicator('Ensemble Güven Skoru')}
                            </th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold cursor-pointer hover:text-white select-none transition-colors" onClick={() => requestSort('Fiyat')}>
                                Fiyat {getSortIndicator('Fiyat')}
                            </th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">İşlemler</th>
                        </tr>
                    </thead>
                    <tbody>
                        {!scanning && scanResults.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="p-12 text-center text-[var(--color-b-muted)]">
                                    <div className="text-5xl mb-4">🔍</div>
                                    Seçili endeks üzerinde 100 farklı teknik indikatörle yapay zeka destekli analiz yapmak için Taramayı Başlatın.
                                </td>
                            </tr>
                        ) : scanning && scanResults.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="p-12 text-center text-[var(--color-b-yellow)]">
                                    <div className="text-5xl mb-4 animate-spin">⏳</div>
                                    Borsadan anlık veriler çekiliyor ve yüzlerce indikatör hesaplanıyor... Lütfen bekleyin.
                                </td>
                            </tr>
                        ) : (
                            sortedResults.map((row: any, i: number) => {
                                const signal = row["Piyasa Kararı"] || "-";
                                const price = row["Fiyat"] || "-";
                                const rsi = row["RSI"] || "-";
                                const score = row["Ensemble Güven Skoru"] || "-";
                                return (
                                <tr key={i} className="hover:bg-[#1e2329] transition-colors border-b border-[var(--color-b-border)]">
                                    <td className="p-4 font-bold text-white text-lg">{row["Hisse"]}</td>
                                    <td className="p-4 font-bold">
                                        <span className={`px-3 py-1 rounded text-sm ${
                                            signal.toLowerCase().includes("güçlü al") ? "bg-[var(--color-b-green)] text-black" :
                                            signal.toLowerCase().includes("al") ? "text-[var(--color-b-green)] border border-[var(--color-b-green)]" :
                                            signal.toLowerCase().includes("güçlü sat") ? "bg-[var(--color-b-red)] text-black" :
                                            signal.toLowerCase().includes("sat") ? "text-[var(--color-b-red)] border border-[var(--color-b-red)]" :
                                            "text-gray-400 border border-gray-600"
                                        }`}>
                                            {signal}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex flex-col">
                                            <span className="text-sm text-white">Güven Skoru: <span className="text-[var(--color-b-yellow)]">{score}</span></span>
                                            <span className="text-sm text-white">RSI: {rsi}</span>
                                        </div>
                                    </td>
                                    <td className="p-4 font-medium text-white">{price}</td>
                                    <td className="p-4">
                                        <div className="flex gap-2">
                                            <button 
                                                onClick={() => router.push(`/?ticker=${row["Hisse"]}`)}
                                                className="text-xs text-[var(--color-b-muted)] hover:text-[var(--color-b-yellow)] border border-[var(--color-b-muted)] hover:border-[var(--color-b-yellow)] px-3 py-1 rounded transition-colors"
                                            >
                                                İncele
                                            </button>
                                            <button 
                                                onClick={() => openModal(row["Hisse"], row["Fiyat"])}
                                                className="text-xs bg-[#1e2329] text-[var(--color-b-green)] hover:bg-[var(--color-b-green)] hover:text-black border border-[var(--color-b-green)] px-3 py-1 rounded transition-colors"
                                            >
                                                Portföye Ekle
                                            </button>
                                            <button 
                                                onClick={() => requireAuth(() => handleAIAnalysis(row))}
                                                className="text-xs flex items-center gap-1 bg-purple-900/20 text-purple-400 hover:bg-purple-600 hover:text-white border border-purple-700/50 px-3 py-1 rounded transition-colors font-bold"
                                            >
                                                <span>✨</span> AI Analiz
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            )})
                        )}
                    </tbody>
                </table>
            </div>

            {/* Portfolio Add Modal */}
            {modalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
                    <div className="bg-[#181a20] border border-[var(--color-b-border)] rounded-lg shadow-xl w-[400px] flex flex-col overflow-hidden">
                        <div className="bg-[#1e2329] p-4 flex justify-between items-center border-b border-[var(--color-b-border)]">
                            <h3 className="font-bold text-lg text-white">Portföye Ekle: {modalTicker}</h3>
                            <button onClick={() => setModalOpen(false)} className="text-[var(--color-b-muted)] hover:text-white">✕</button>
                        </div>
                        <form onSubmit={handlePortfolioAdd} className="p-6 flex flex-col gap-4">
                            <div>
                                <label className="block text-sm text-[var(--color-b-muted)] mb-1">Hisse Kodu</label>
                                <input type="text" value={modalTicker} disabled className="w-full bg-[#2b3139] border border-[var(--color-b-border)] rounded p-2 text-white disabled:opacity-70" />
                            </div>
                            <div>
                                <label className="block text-sm text-[var(--color-b-muted)] mb-1">Maliyet Fiyatı</label>
                                <input 
                                    type="number" 
                                    step="0.01" 
                                    required 
                                    value={modalPrice} 
                                    onChange={(e) => setModalPrice(e.target.value)}
                                    className="w-full bg-[#181a20] border border-[var(--color-b-border)] focus:border-[var(--color-b-yellow)] focus:outline-none rounded p-2 text-white" 
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-[var(--color-b-muted)] mb-1">Adet</label>
                                <input 
                                    type="number" 
                                    required 
                                    min="1"
                                    value={modalQty} 
                                    onChange={(e) => setModalQty(e.target.value)}
                                    className="w-full bg-[#181a20] border border-[var(--color-b-border)] focus:border-[var(--color-b-yellow)] focus:outline-none rounded p-2 text-white" 
                                />
                            </div>
                            
                            <div className="mt-4 flex gap-3">
                                <button type="button" onClick={() => setModalOpen(false)} className="flex-1 p-2 rounded border border-[var(--color-b-border)] hover:bg-[#2b3139] transition-colors">
                                    İptal
                                </button>
                                <button type="submit" className="flex-1 p-2 rounded bg-[var(--color-b-yellow)] text-black font-bold hover:bg-yellow-500 transition-colors">
                                    Satın Al (Kaydet)
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

        <AIAnalyzeModal 
            isOpen={aiModalOpen}
            onClose={() => setAiModalOpen(false)}
            {...aiProps}
        />
        </div>
        <AuthModal />
        </>
    );
}
