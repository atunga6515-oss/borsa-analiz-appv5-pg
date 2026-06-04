"use client";
import { useState } from "react";

export default function AlarmsPage() {
    return (
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="mb-6 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">🔔 Alarm Merkezi</h1>
                    <p className="text-[var(--color-b-muted)]">Fiyat veya İndikatör Şartları Gerçekleştiğinde Bildirim Alın</p>
                </div>
                <button className="px-6 py-3 bg-[var(--color-b-yellow)] text-black font-bold rounded hover:bg-yellow-500 transition-colors">
                    + Yeni Alarm Kur
                </button>
            </div>

            <div className="glass-panel p-6 rounded-lg mb-6">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-[#1e2329] text-[var(--color-b-muted)] text-sm">
                        <tr>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Hisse</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Koşul</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Hedef Değer</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold">Durum</th>
                            <th className="p-4 border-b border-[var(--color-b-border)] font-semibold text-right">İşlem</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr className="hover:bg-[#1e2329] transition-colors border-b border-[var(--color-b-border)]">
                            <td className="p-4 font-bold text-white">THYAO</td>
                            <td className="p-4">Fiyat Şunu Geçerse (Yukarı)</td>
                            <td className="p-4 font-bold text-[var(--color-b-green)]">325.00</td>
                            <td className="p-4"><span className="px-2 py-1 bg-[var(--color-b-yellow)] text-black rounded text-xs">Aktif</span></td>
                            <td className="p-4 text-right">
                                <button className="text-xs text-[var(--color-b-red)] hover:text-red-400">Sil</button>
                            </td>
                        </tr>
                        <tr className="hover:bg-[#1e2329] transition-colors border-b border-[var(--color-b-border)]">
                            <td className="p-4 font-bold text-white">FROTO</td>
                            <td className="p-4">RSI Şundan Düşükse (Aşırı Satım)</td>
                            <td className="p-4 font-bold text-[var(--color-b-green)]">30.0</td>
                            <td className="p-4"><span className="px-2 py-1 bg-gray-600 text-white rounded text-xs">Beklemede</span></td>
                            <td className="p-4 text-right">
                                <button className="text-xs text-[var(--color-b-red)] hover:text-red-400">Sil</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <p className="text-xs text-[var(--color-b-muted)] text-center">API bağlantıları yapılandırılıyor...</p>
        </div>
    );
}
