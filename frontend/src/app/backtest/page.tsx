"use client";
import { useState } from "react";
import api from "@/lib/api";
import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function BacktestPage() {
    const { requireAuth, AuthModal } = useRequireAuth();
    const [ticker, setTicker] = useState("THYAO");
    const [capital, setCapital] = useState(100000);
    const [days, setDays] = useState(180);
    const [buyThreshold, setBuyThreshold] = useState(65);
    const [sellThreshold, setSellThreshold] = useState(45);
    const [stopLoss, setStopLoss] = useState(5);
    const [takeProfit, setTakeProfit] = useState(15);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    const runBacktest = async () => {
        if (!ticker) return;
        setLoading(true);
        try {
            const res = await api.post('/backtest/', {
                ticker: ticker.toUpperCase(),
                initial_capital: capital,
                lookback_days: days,
                buy_threshold: buyThreshold,
                sell_threshold: sellThreshold,
                stop_loss_pct: stopLoss,
                take_profit_pct: takeProfit
            });
            if (res.data) {
                setResult(res.data);
            }
        } catch (error) {
            console.error("Backtest hatası", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">💼 Gelişmiş Backtest Modülü</h1>
                <p className="text-[var(--color-b-muted)]">100 İndikatörlü AI Sinyallerinin Geçmiş Performans Testi</p>
            </div>

            <div className="glass-panel p-6 rounded-lg mb-6 flex gap-6 flex-wrap items-end border border-[var(--color-b-border)]">
                <div>
                    <label className="block text-sm text-[var(--color-b-muted)] mb-2">Hisse Kodu</label>
                    <input 
                        type="text" 
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value)}
                        className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white font-bold w-48 focus:outline-none focus:border-[var(--color-b-yellow)]"
                    />
                </div>
                <div>
                    <label className="block text-sm text-[var(--color-b-muted)] mb-2">Başlangıç Sermayesi (₺)</label>
                    <input 
                        type="number" 
                        value={capital}
                        onChange={(e) => setCapital(Number(e.target.value))}
                        className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white font-bold w-48 focus:outline-none focus:border-[var(--color-b-yellow)]"
                    />
                </div>
                <div>
                    <label className="block text-sm text-[var(--color-b-muted)] mb-2">Test Süresi (Gün)</label>
                    <select 
                        value={days}
                        onChange={(e) => setDays(Number(e.target.value))}
                        className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white font-bold w-48 focus:outline-none focus:border-[var(--color-b-yellow)]"
                    >
                        <option value={90}>Son 3 Ay (90 Gün)</option>
                        <option value={180}>Son 6 Ay (180 Gün)</option>
                        <option value={365}>Son 1 Yıl (365 Gün)</option>
                    </select>
                </div>
                
                {/* Yeni Parametreler */}
                <div>
                    <label className="block text-sm text-[var(--color-b-muted)] mb-2">Alım Skoru (≥)</label>
                    <input 
                        type="number" 
                        value={buyThreshold}
                        onChange={(e) => setBuyThreshold(Number(e.target.value))}
                        className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-[var(--color-b-green)] font-bold w-32 focus:outline-none focus:border-[var(--color-b-yellow)]"
                    />
                </div>
                <div>
                    <label className="block text-sm text-[var(--color-b-muted)] mb-2">Satım Skoru (≤)</label>
                    <input 
                        type="number" 
                        value={sellThreshold}
                        onChange={(e) => setSellThreshold(Number(e.target.value))}
                        className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-[var(--color-b-red)] font-bold w-32 focus:outline-none focus:border-[var(--color-b-yellow)]"
                    />
                </div>
                <div>
                    <label className="block text-sm text-[var(--color-b-muted)] mb-2">Stop Loss (%)</label>
                    <input 
                        type="number" 
                        value={stopLoss}
                        onChange={(e) => setStopLoss(Number(e.target.value))}
                        className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-[var(--color-b-red)] font-bold w-32 focus:outline-none focus:border-[var(--color-b-yellow)]"
                    />
                </div>
                <div>
                    <label className="block text-sm text-[var(--color-b-muted)] mb-2">Take Profit (%)</label>
                    <input 
                        type="number" 
                        value={takeProfit}
                        onChange={(e) => setTakeProfit(Number(e.target.value))}
                        className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-[var(--color-b-green)] font-bold w-32 focus:outline-none focus:border-[var(--color-b-yellow)]"
                    />
                </div>

                <button 
                    onClick={() => requireAuth(runBacktest)}
                    disabled={loading}
                    className="px-8 py-3 bg-[var(--color-b-yellow)] text-black font-bold rounded hover:bg-yellow-500 transition-colors disabled:opacity-50"
                >
                    {loading ? "Simüle Ediliyor..." : "Testi Başlat"}
                </button>
            </div>

            {result && !result.error && (
                <>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                    <div className="glass-panel p-6 rounded-lg text-center border-l-4 border-[var(--color-b-green)]">
                        <p className="text-[var(--color-b-muted)] mb-2">Net Getiri</p>
                        <h2 className={`text-3xl font-bold ${result.total_return_pct > 0 ? "text-[var(--color-b-green)]" : "text-[var(--color-b-red)]"}`}>
                            %{result.total_return_pct?.toFixed(2)}
                        </h2>
                    </div>
                    <div className="glass-panel p-6 rounded-lg text-center border-l-4 border-white">
                        <p className="text-[var(--color-b-muted)] mb-2">Mevduat (Risksiz) Getirisi</p>
                        <h2 className="text-3xl font-bold text-white">
                            %{result.risk_free_return_pct?.toFixed(2)}
                        </h2>
                    </div>
                    <div className="glass-panel p-6 rounded-lg text-center border-l-4 border-[var(--color-b-yellow)]">
                        <p className="text-[var(--color-b-muted)] mb-2">Başarı Oranı (Win Rate)</p>
                        <h2 className={`text-3xl font-bold ${result.win_rate > 50 ? "text-[var(--color-b-green)]" : "text-[var(--color-b-red)]"}`}>
                            %{result.win_rate?.toFixed(1)}
                        </h2>
                    </div>
                    <div className="glass-panel p-6 rounded-lg text-center border-l-4 border-[var(--color-b-red)]">
                        <p className="text-[var(--color-b-muted)] mb-2">Max Drawdown (Zarar)</p>
                        <h2 className="text-3xl font-bold text-[var(--color-b-red)]">
                            %{result.max_drawdown_pct?.toFixed(2)}
                        </h2>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div className="glass-panel p-6 rounded-lg text-center border-l-4 border-blue-500">
                        <p className="text-[var(--color-b-muted)] mb-2">Al/Sat İşlem Sayısı</p>
                        <h2 className="text-3xl font-bold text-white">
                            {result.number_of_trades} İşlem
                        </h2>
                    </div>
                    <div className="glass-panel p-6 rounded-lg text-center border-l-4 border-purple-500">
                        <p className="text-[var(--color-b-muted)] mb-2">Kâr Faktörü (Profit Factor)</p>
                        <h2 className={`text-3xl font-bold ${result.profit_factor > 1 ? "text-[var(--color-b-green)]" : "text-[var(--color-b-red)]"}`}>
                            {result.profit_factor?.toFixed(2)}
                        </h2>
                    </div>
                    <div className="glass-panel p-6 rounded-lg text-center border-l-4 border-orange-500">
                        <p className="text-[var(--color-b-muted)] mb-2">Sharpe Oranı</p>
                        <h2 className="text-3xl font-bold text-white">
                            {result.sharpe_ratio?.toFixed(2)}
                        </h2>
                    </div>
                </div>
                </>
            )}
            
            {result && result.error && (
                <div className="bg-red-500/10 text-red-400 p-4 rounded border border-red-500/30">
                    {result.error}
                </div>
            )}
        </div>
        <AuthModal />
        </>
    );
}
