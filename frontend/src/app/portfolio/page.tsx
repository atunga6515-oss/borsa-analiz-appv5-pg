"use client";
import { useState, useEffect } from "react";
import api from "@/lib/api";

export default function PortfolioPage() {
    const [positions, setPositions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchPortfolio();
    }, []);

    const fetchPortfolio = async () => {
        setLoading(true);
        try {
            const res = await api.get('/portfolio');
            if (res.data && res.data.data) {
                setPositions(res.data.data);
            }
        } catch (error) {
            console.error("Portföy yüklenemedi:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)]">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">💼 Sanal Portföy</h1>
                    <p className="text-[var(--color-b-muted)]">Açık pozisyonlarınızı ve kâr/zarar durumunuzu takip edin</p>
                </div>
                <button 
                    className="px-6 py-3 bg-[var(--color-b-green)] text-black font-bold rounded hover:bg-green-500 transition-colors"
                >
                    + Yeni İşlem Ekle
                </button>
            </div>
            
            <div className="glass-panel flex-1 overflow-auto rounded-lg">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-[#1e2329] text-[var(--color-b-muted)] text-sm sticky top-0">
                        <tr>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Hisse</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Adet</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Maliyet</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Tarih</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold text-right">İşlem</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan={5} className="p-12 text-center text-[var(--color-b-muted)]">
                                    Yükleniyor...
                                </td>
                            </tr>
                        ) : positions.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="p-12 text-center text-[var(--color-b-muted)]">
                                    <div className="text-5xl mb-4">💼</div>
                                    Henüz açık pozisyonunuz bulunmuyor.
                                </td>
                            </tr>
                        ) : (
                            positions.map((row: any, i: number) => {
                                return (
                                <tr key={i} className="hover:bg-[#1e2329] transition-colors border-b border-[var(--color-b-border)]">
                                    <td className="p-4 font-bold text-[var(--color-b-yellow)] text-lg">{row.ticker}</td>
                                    <td className="p-4 text-white font-medium">{row.adet} Lot</td>
                                    <td className="p-4 text-white font-medium">{row.fiyat} ₺</td>
                                    <td className="p-4 text-[var(--color-b-muted)]">{row.tarih}</td>
                                    <td className="p-4 text-right">
                                        <button className="text-xs bg-[var(--color-b-red)] text-black font-bold px-3 py-1 rounded hover:bg-red-500 transition-colors">
                                            Pozisyonu Kapat
                                        </button>
                                    </td>
                                </tr>
                            )})
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
