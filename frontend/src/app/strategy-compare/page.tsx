"use client";
import { useState } from "react";

export default function StrategyComparePage() {
    return (
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)] overflow-y-auto">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">🧪 Strateji Karşılaştırma Motoru</h1>
                <p className="text-[var(--color-b-muted)]">Farklı Algoritmaların Performans Çarpışması</p>
            </div>

            <div className="glass-panel p-6 rounded-lg mb-6 flex gap-4">
                <select className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white font-bold w-48 focus:outline-none">
                    <option>Hisse: THYAO</option>
                    <option>Hisse: EREGL</option>
                    <option>Hisse: ASELS</option>
                </select>
                <select className="p-3 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white font-bold w-48 focus:outline-none">
                    <option>Zaman: Son 1 Yıl</option>
                    <option>Zaman: Son 6 Ay</option>
                </select>
                <button className="px-6 py-3 bg-[var(--color-b-yellow)] text-black font-bold rounded hover:bg-yellow-500 transition-colors">
                    Stratejileri Yarıştır
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="glass-panel p-6 rounded-lg border-t-4 border-[var(--color-b-green)]">
                    <h2 className="text-xl font-bold text-white mb-4">V6 Hibrit Algoritma</h2>
                    <div className="text-4xl font-bold text-[var(--color-b-green)] mb-2">%84.5</div>
                    <p className="text-[var(--color-b-muted)] text-sm">Yıllık Net Getiri</p>
                    <hr className="border-[var(--color-b-border)] my-4" />
                    <p className="text-sm text-white">İşlem Sayısı: <span className="float-right font-bold">42</span></p>
                    <p className="text-sm text-white mt-2">Max Drawdown: <span className="float-right font-bold text-[var(--color-b-red)]">-%12.4</span></p>
                </div>
                
                <div className="glass-panel p-6 rounded-lg border-t-4 border-blue-500">
                    <h2 className="text-xl font-bold text-white mb-4">Muhafazakar (MACD+RSI)</h2>
                    <div className="text-4xl font-bold text-blue-400 mb-2">%45.2</div>
                    <p className="text-[var(--color-b-muted)] text-sm">Yıllık Net Getiri</p>
                    <hr className="border-[var(--color-b-border)] my-4" />
                    <p className="text-sm text-white">İşlem Sayısı: <span className="float-right font-bold">18</span></p>
                    <p className="text-sm text-white mt-2">Max Drawdown: <span className="float-right font-bold text-[var(--color-b-red)]">-%5.1</span></p>
                </div>

                <div className="glass-panel p-6 rounded-lg border-t-4 border-purple-500">
                    <h2 className="text-xl font-bold text-white mb-4">Agresif (SMC+Momentum)</h2>
                    <div className="text-4xl font-bold text-purple-400 mb-2">%112.8</div>
                    <p className="text-[var(--color-b-muted)] text-sm">Yıllık Net Getiri</p>
                    <hr className="border-[var(--color-b-border)] my-4" />
                    <p className="text-sm text-white">İşlem Sayısı: <span className="float-right font-bold">156</span></p>
                    <p className="text-sm text-white mt-2">Max Drawdown: <span className="float-right font-bold text-[var(--color-b-red)]">-%28.9</span></p>
                </div>
            </div>
            
            <p className="text-xs text-[var(--color-b-muted)] text-center">API bağlantıları yapılandırılıyor...</p>
        </div>
    );
}
