"use client";
import { useState } from "react";
import api from "@/lib/api";
import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function KapPage() {
    const { requireAuth, AuthModal } = useRequireAuth();
    const [ticker, setTicker] = useState("");
    const [loading, setLoading] = useState(false);
    const [kapData, setKapData] = useState<any>(null);

    const fetchKap = async () => {
        if (!ticker) return;
        setLoading(true);
        try {
            const res = await api.get(`/kap/${ticker}`);
            if (res.data) {
                setKapData(res.data);
            }
        } catch (error) {
            console.error("KAP verisi çekilemedi", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">📰 KAP Haber Analizi (Yapay Zeka)</h1>
                    <p className="text-[var(--color-b-muted)]">KAP Bildirimlerinin Otomatik Duygu Analizi (NLP)</p>
                </div>
            </div>

            <div className="flex gap-4 mb-6">
                <input 
                    type="text" 
                    placeholder="Hisse Kodu (Örn: THYAO)"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white font-bold w-64 focus:outline-none focus:border-[var(--color-b-yellow)]"
                />
                <button 
                    onClick={() => requireAuth(fetchKap)}
                    disabled={loading}
                    className="px-6 py-3 bg-[var(--color-b-yellow)] text-black font-bold rounded hover:bg-yellow-500 transition-colors disabled:opacity-50"
                >
                    {loading ? "Analiz Ediliyor..." : "Haberleri Analiz Et"}
                </button>
            </div>

            {kapData && (
                <div className="mb-6 p-6 glass-panel rounded-lg flex items-center justify-between border-l-4 border-[var(--color-b-yellow)]">
                    <div>
                        <h2 className="text-xl font-bold text-white mb-1">Genel Duygu Skoru</h2>
                        <p className="text-[var(--color-b-muted)] text-sm">(-100 ile +100 arası AI değerlendirmesi)</p>
                    </div>
                    <div className={`text-4xl font-bold ${kapData.avg_score > 0 ? "text-[var(--color-b-green)]" : kapData.avg_score < 0 ? "text-[var(--color-b-red)]" : "text-white"}`}>
                        {kapData.avg_score > 0 ? "+" : ""}{kapData.avg_score}
                    </div>
                </div>
            )}
            
            <div className="glass-panel flex-1 overflow-auto rounded-lg">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-[#1e2329] text-[var(--color-b-muted)] text-sm sticky top-0">
                        <tr>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold w-1/5">Tarih</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold w-2/5">Haber Başlığı</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold w-1/5 text-center">Kategori</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold w-1/5 text-center">AI Skoru</th>
                        </tr>
                    </thead>
                    <tbody>
                        {!kapData ? (
                            <tr>
                                <td colSpan={3} className="p-12 text-center text-[var(--color-b-muted)]">
                                    <div className="text-5xl mb-4">📰</div>
                                    Hisse kodu girerek KAP bildirimlerinin NLP analizini başlatın.
                                </td>
                            </tr>
                        ) : kapData.results && kapData.results.length === 0 ? (
                            <tr>
                                <td colSpan={3} className="p-12 text-center text-[var(--color-b-muted)]">
                                    Son zamanlarda bu hisseye ait haber bulunamadı.
                                </td>
                            </tr>
                        ) : (
                            kapData.results.map((row: any, i: number) => {
                                return (
                                <tr key={i} className="hover:bg-[#1e2329] transition-colors border-b border-[var(--color-b-border)]">
                                    <td className="p-4 text-[var(--color-b-muted)]">{row.date_str || "-"}</td>
                                    <td className="p-4 text-white font-medium">
                                        <p>{row.title || "-"}</p>
                                        <p className="text-xs text-[var(--color-b-muted)] mt-1">{row.reason || ""}</p>
                                    </td>
                                    <td className="p-4 text-center text-sm font-bold text-[#a5b1c2]">{row.category || "-"}</td>
                                    <td className="p-4 text-center">
                                        <span className={`px-3 py-1 rounded text-sm font-bold ${
                                            row.score > 0.1 ? "text-[var(--color-b-green)] border border-[var(--color-b-green)]" : 
                                            row.score < -0.1 ? "text-[var(--color-b-red)] border border-[var(--color-b-red)]" : 
                                            "text-gray-400 border border-gray-600"
                                        }`}>
                                            {row.score > 0 ? "+" : ""}{row.score}
                                        </span>
                                    </td>
                                </tr>
                            )})
                        )}
                    </tbody>
                </table>
            </div>
        </div>
        <AuthModal />
        </>
    );
}
