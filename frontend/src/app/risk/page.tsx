"use client";
import { useState } from "react";
import api from "@/lib/api";

export default function RiskPage() {
    return (
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">⚠️ Risk Yönetim Merkezi</h1>
                <p className="text-[var(--color-b-muted)]">Portföyünüzün Volatilite ve Beta Analizleri</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="glass-panel p-6 rounded-lg">
                    <h2 className="text-xl font-bold text-white mb-4">Portföy Beta Değeri (Piyasa Riski)</h2>
                    <div className="flex items-center gap-4">
                        <div className="text-4xl font-bold text-[var(--color-b-yellow)]">1.24</div>
                        <div className="text-sm text-[var(--color-b-muted)]">Piyasadan %24 daha hareketli. Agresif bir portföy.</div>
                    </div>
                </div>
                
                <div className="glass-panel p-6 rounded-lg">
                    <h2 className="text-xl font-bold text-white mb-4">Maksimum Kayıp İhtimali (VaR)</h2>
                    <div className="flex items-center gap-4">
                        <div className="text-4xl font-bold text-[var(--color-b-red)]">-%4.5</div>
                        <div className="text-sm text-[var(--color-b-muted)]">Günlük %95 güven aralığında tahmini maksimum kayıp.</div>
                    </div>
                </div>
            </div>

            <div className="glass-panel p-6 rounded-lg mb-6">
                <h2 className="text-xl font-bold text-white mb-4">Aktif İşlemler İçin Dinamik Stop-Loss Önerileri</h2>
                <table className="w-full text-left border-collapse">
                    <thead className="bg-[#1e2329] text-[var(--color-b-muted)] text-sm">
                        <tr>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Hisse</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Alış Maliyeti</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Anlık Fiyat</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Önerilen Stop (ATR)</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Risk Durumu</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr className="hover:bg-[#1e2329] transition-colors border-b border-[var(--color-b-border)]">
                            <td className="p-4 font-bold text-white">THYAO</td>
                            <td className="p-4">300.50</td>
                            <td className="p-4 text-[var(--color-b-green)]">315.20</td>
                            <td className="p-4 text-[var(--color-b-yellow)] font-bold">295.00</td>
                            <td className="p-4"><span className="px-2 py-1 bg-[var(--color-b-green)] text-black rounded text-xs">Düşük</span></td>
                        </tr>
                        <tr className="hover:bg-[#1e2329] transition-colors border-b border-[var(--color-b-border)]">
                            <td className="p-4 font-bold text-white">SASA</td>
                            <td className="p-4">45.00</td>
                            <td className="p-4 text-[var(--color-b-red)]">42.10</td>
                            <td className="p-4 text-[var(--color-b-red)] font-bold">40.50</td>
                            <td className="p-4"><span className="px-2 py-1 bg-[var(--color-b-red)] text-black rounded text-xs">Yüksek</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <p className="text-xs text-[var(--color-b-muted)] text-center mt-4">API bağlantıları yapılandırılıyor...</p>
        </div>
    );
}
