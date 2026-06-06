"use client";
import { useState, useEffect } from "react";
import api from "@/lib/api";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import AIAnalyzeModal from "../components/AIAnalyzeModal";

export default function PortfolioPage() {
    const { requireAuth, AuthModal } = useRequireAuth();
    const [positions, setPositions] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Modal state
    const [showModal, setShowModal] = useState(false);
    const [newTicker, setNewTicker] = useState("");
    const [newQuantity, setNewQuantity] = useState("");
    const [newPrice, setNewPrice] = useState("");

    // AI Modal State
    const [aiModalOpen, setAiModalOpen] = useState(false);
    const [aiProps, setAiProps] = useState<any>({ ticker: "", price: 0 });
    const [newDate, setNewDate] = useState("");


    useEffect(() => {
        fetchPortfolio();
    }, []);

    const fetchPortfolio = async () => {
        setLoading(true);
        try {
            const res = await api.get('/portfolio/');
            if (res.data && res.data.data) {
                setPositions(res.data.data);
            }
        } catch (error) {
            console.error("Portföy yüklenemedi:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddTransaction = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.post('/portfolio/transaction', {
                ticker: newTicker,
                type: "ALIS",
                quantity: parseFloat(newQuantity),
                price: parseFloat(newPrice),
                date: newDate || undefined
            });
            setShowModal(false);
            setNewTicker("");
            setNewQuantity("");
            setNewPrice("");
            setNewDate("");
            fetchPortfolio();
        } catch (error) {
            console.error("İşlem eklenemedi:", error);
            alert("İşlem eklenirken hata oluştu.");
        }
    };


    return (
        <>
        <div className="flex w-full h-full p-6 flex-col bg-[var(--color-b-bg)] text-[var(--color-b-text)]">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">💼 Sanal Portföy</h1>
                    <p className="text-[var(--color-b-muted)]">Açık pozisyonlarınızı ve kâr/zarar durumunuzu takip edin</p>
                </div>
                <button 
                    onClick={() => requireAuth(() => setShowModal(true))}
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
                                    <td className="p-4 text-white font-medium">{row.alis_fiyati} ₺</td>
                                    <td className="p-4 text-[var(--color-b-muted)]">{row.alis_tarihi}</td>
                                    <td className="p-4 text-right flex justify-end gap-2">
                                        <button 
                                            onClick={() => {
                                                setAiProps({ ticker: row.ticker, price: row.alis_fiyati });
                                                setAiModalOpen(true);
                                            }}
                                            className="text-xs bg-purple-900/50 text-purple-300 border border-purple-700 font-bold px-3 py-1 rounded hover:bg-purple-600 hover:text-white transition-colors"
                                        >
                                            ✨ AI Analiz
                                        </button>
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
            
            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
                    <div className="bg-[#181a20] p-6 rounded-lg border border-[var(--color-b-border)] w-96 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-4">Yeni İşlem Ekle (Alış)</h2>
                        <form onSubmit={handleAddTransaction} className="flex flex-col gap-4">
                            <div>
                                <label className="block text-sm text-[var(--color-b-muted)] mb-1">Hisse Kodu</label>
                                <input 
                                    type="text" 
                                    required 
                                    value={newTicker}
                                    onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
                                    className="w-full p-2 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white focus:outline-none focus:border-[var(--color-b-yellow)]" 
                                    placeholder="Örn: THYAO" 
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-[var(--color-b-muted)] mb-1">Adet (Lot)</label>
                                <input 
                                    type="number" 
                                    required 
                                    min="0.1" 
                                    step="0.1"
                                    value={newQuantity}
                                    onChange={(e) => setNewQuantity(e.target.value)}
                                    className="w-full p-2 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white focus:outline-none focus:border-[var(--color-b-yellow)]" 
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-[var(--color-b-muted)] mb-1">Maliyet (Alış Fiyatı) ₺</label>
                                <input 
                                    type="number" 
                                    required 
                                    min="0.01" 
                                    step="0.01"
                                    value={newPrice}
                                    onChange={(e) => setNewPrice(e.target.value)}
                                    className="w-full p-2 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-white focus:outline-none focus:border-[var(--color-b-yellow)]" 
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-[var(--color-b-muted)] mb-1">Alış Tarihi (Opsiyonel)</label>
                                <input 
                                    type="datetime-local" 
                                    value={newDate}
                                    onChange={(e) => setNewDate(e.target.value)}
                                    className="w-full p-2 bg-[#1e2329] border border-[var(--color-b-border)] rounded text-[var(--color-b-muted)] focus:outline-none focus:border-[var(--color-b-yellow)]" 
                                />
                            </div>
                            <div className="flex justify-end gap-3 mt-4">
                                <button 
                                    type="button" 
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 border border-[var(--color-b-border)] rounded text-[var(--color-b-muted)] hover:text-white"
                                >
                                    İptal
                                </button>
                                <button 
                                    type="submit" 
                                    className="px-4 py-2 bg-[var(--color-b-green)] text-black font-bold rounded hover:bg-green-500"
                                >
                                    Kaydet
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
        <AuthModal />
        </>
    );
}
