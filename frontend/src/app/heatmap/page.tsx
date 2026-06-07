"use client";
import { useState, useEffect } from "react";
import api from "@/lib/api";

export default function HeatmapPage() {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchHeatmap();
    }, []);

    const fetchHeatmap = async () => {
        try {
            const res = await api.get('/market/heatmap');
            if (res.data && res.data.data) {
                setData(res.data.data);
            }
        } catch (err: any) {
            setError("Harita yüklenemedi: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    // Group by sector
    const sectors: { [key: string]: any[] } = {};
    data.forEach(item => {
        if (!sectors[item.sector]) sectors[item.sector] = [];
        sectors[item.sector].push(item);
    });

    const getBgColor = (change: number) => {
        if (change >= 3) return "bg-green-600";
        if (change > 0) return "bg-green-500/80";
        if (change === 0) return "bg-gray-600";
        if (change > -3) return "bg-red-500/80";
        return "bg-red-600";
    };

    return (
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-auto">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">🗺️ Sektörel Isı Haritası</h1>
                <p className="text-[var(--color-b-muted)]">BIST 100 ana hisselerinin sektörel bazda anlık performans görünümü</p>
            </div>

            {loading ? (
                <div className="flex-1 flex justify-center items-center text-xl text-[var(--color-b-muted)]">
                    Harita yükleniyor (Canlı fiyatlar çekiliyor)...
                </div>
            ) : error ? (
                <div className="text-red-500 bg-red-900/20 p-4 rounded">{error}</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {Object.keys(sectors).map(sectorName => (
                        <div key={sectorName} className="bg-[#1e2329] rounded border border-[var(--color-b-border)] p-4">
                            <h2 className="text-lg font-bold text-white mb-3 border-b border-[var(--color-b-border)] pb-2">{sectorName}</h2>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                {sectors[sectorName].sort((a, b) => b.volume - a.volume).map(item => (
                                    <div 
                                        key={item.ticker} 
                                        className={`p-3 rounded text-center flex flex-col justify-center shadow-lg transition-transform hover:scale-105 cursor-pointer ${getBgColor(item.change)} text-white`}
                                    >
                                        <div className="font-bold text-lg">{item.ticker}</div>
                                        <div className="text-sm font-medium">{item.price} ₺</div>
                                        <div className="text-xs opacity-90">{item.change > 0 ? "+" : ""}{item.change}%</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
