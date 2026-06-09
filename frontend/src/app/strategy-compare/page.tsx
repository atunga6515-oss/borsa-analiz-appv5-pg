"use client";
import { useState } from "react";
import api from "@/lib/api";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import SymbolAutocomplete from "@/components/SymbolAutocomplete";

export default function StrategyComparePage() {
    const { requireAuth, AuthModal } = useRequireAuth();
    const [ticker, setTicker] = useState("THYAO");
    const [period, setPeriod] = useState("1y");
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any[]>([]);

    const handleCompare = async () => {
        if (!ticker) return;
        setLoading(true);
        try {
            const res = await api.post('/backtest/compare', {
                ticker: ticker,
                period: period === "Son 6 Ay" ? "6mo" : period === "Son 2 Yıl" ? "2y" : "1y"
            });
            if (res.data && res.data.data) {
                setResults(res.data.data);
            } else if (res.data && res.data.error) {
                alert(res.data.error);
            }
        } catch (error) {
            console.error("Comparison error:", error);
            alert("Analiz sırasında hata oluştu.");
        } finally {
            setLoading(false);
        }
    };
    return (
        <>
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">🧪 Strateji Karşılaştırma Motoru</h1>
                <p className="text-[var(--color-b-muted)]">Farklı Algoritmaların Performans Çarpışması</p>
            </div>

            <div className="glass-panel p-6 rounded-lg mb-6 flex gap-4">
                <SymbolAutocomplete 
                    value={ticker}
                    onChange={(val) => setTicker(val)}
                    placeholder="Hisse Giriniz (Örn: THYAO, ASELS)"
                    className="w-64"
                />
                <select 
                    className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white font-bold w-48 focus:outline-none"
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                >
                    <option value="1y">Zaman: Son 1 Yıl</option>
                    <option value="6mo">Zaman: Son 6 Ay</option>
                    <option value="2y">Zaman: Son 2 Yıl</option>
                </select>
                <button 
                    onClick={() => requireAuth(handleCompare)}
                    disabled={loading}
                    className="px-6 py-3 bg-[var(--color-b-yellow)] text-black font-bold rounded hover:bg-yellow-500 transition-colors disabled:opacity-50"
                >
                    {loading ? "Hesaplanıyor..." : "Stratejileri Yarıştır"}
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                {results.length > 0 ? (
                    results.map((res: any, idx: number) => {
                        const getiri = res['Toplam Getiri (%)'];
                        const isPositive = getiri >= 0;
                        const dd = res['Maks Düşüş (%)'];
                        return (
                            <div key={idx} className={`glass-panel p-6 rounded-lg border-t-4 ${isPositive ? 'border-[var(--color-b-green)]' : 'border-[var(--color-b-red)]'}`}>
                                <h2 className="text-xl font-bold text-white mb-4">{res['Strateji']}</h2>
                                <div className={`text-4xl font-bold mb-2 ${isPositive ? 'text-[var(--color-b-green)]' : 'text-[var(--color-b-red)]'}`}>
                                    {isPositive ? '+' : ''}{getiri}%
                                </div>
                                <p className="text-[var(--color-b-muted)] text-sm">Yıllık Net Getiri</p>
                                <hr className="border-[var(--color-b-border)] my-4" />
                                <p className="text-sm text-white">İşlem Sayısı: <span className="float-right font-bold">{res['Toplam İşlem']}</span></p>
                                <p className="text-sm text-white mt-2">Max Drawdown: <span className="float-right font-bold text-[var(--color-b-red)]">-{dd}%</span></p>
                                <p className="text-sm text-white mt-2">Win Rate: <span className="float-right font-bold text-blue-400">%{res['Kazanma Oranı (%)']}</span></p>
                                <p className="text-sm text-white mt-2">Sharpe: <span className="float-right font-bold text-purple-400">{res['Sharpe Oranı']}</span></p>
                            </div>
                        );
                    })
                ) : (
                    <div className="col-span-3 text-center text-[var(--color-b-muted)] p-12">
                        {loading ? "Analiz yapılıyor, lütfen bekleyin (Bu işlem yaklaşık 10-20 saniye sürebilir)..." : "Analiz başlatmak için yukarıdan hisse girip butona tıklayın."}
                    </div>
                )}
            </div>
        </div>
        <AuthModal />
        </>
    );
}
