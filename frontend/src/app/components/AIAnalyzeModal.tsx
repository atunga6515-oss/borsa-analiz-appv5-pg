"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface AIModalProps {
    isOpen: boolean;
    onClose: () => void;
    ticker: string;
    price: number;
    rsi?: number;
    macd_signal?: string;
    trend?: string;
    note?: string;
}

export default function AIAnalyzeModal({ isOpen, onClose, ticker, price, rsi, macd_signal, trend, note }: AIModalProps) {
    const [step, setStep] = useState<"CONFIRM" | "LOADING" | "RESULT" | "ERROR">("CONFIRM");
    const [quota, setQuota] = useState<number | null>(null);
    const [resultText, setResultText] = useState("");
    const [errorText, setErrorText] = useState("");

    useEffect(() => {
        if (isOpen) {
            setStep("CONFIRM");
            setQuota(null);
            setResultText("");
            setErrorText("");
            api.get("/auth/me").then(res => {
                setQuota(res.data.ai_quota);
            }).catch(err => {
                console.error("Quota fetch error", err);
                setQuota(0);
            });
        }
    }, [isOpen]);

    const handleAnalyze = async () => {
        if (quota !== null && quota <= 0) {
            setStep("ERROR");
            setErrorText("Yapay Zeka analiz kotanız bitmiştir. Lütfen yöneticinizle iletişime geçin.");
            return;
        }

        setStep("LOADING");
        try {
            const res = await api.post('/ai/analyze', {
                ticker,
                price,
                rsi: rsi || 0,
                macd_signal: macd_signal || "Bilinmiyor",
                trend: trend || "Bilinmiyor",
                note: note || ""
            });
            setResultText(res.data.analysis);
            setStep("RESULT");
        } catch(error: any) {
            console.error("AI Hatası:", error);
            setErrorText(error.response?.data?.detail || "AI analizi sırasında bir hata oluştu.");
            setStep("ERROR");
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-[#181a20] border border-gray-800 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
                <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-[#1e2329]">
                    <h3 className="font-bold text-white flex items-center gap-2">
                        <span>🤖</span> Yapay Zeka Broker Analizi: <span className="text-[var(--color-b-yellow)]">{ticker}</span>
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        ✕
                    </button>
                </div>

                <div className="p-6 overflow-y-auto">
                    {step === "CONFIRM" && (
                        <div className="text-center py-6">
                            <div className="text-4xl mb-4">🔮</div>
                            <h4 className="text-xl font-bold text-white mb-2">{ticker} Analiz Edilsin mi?</h4>
                            <p className="text-gray-400 mb-6">Yapay zeka asistanı sizin için güncel teknik verileri yorumlayacaktır.</p>
                            
                            <div className="bg-[#1e2329] p-4 rounded-lg inline-block mb-8 border border-gray-800 min-w-[200px]">
                                <p className="text-sm text-gray-400 mb-1">Kalan Kotanız</p>
                                {quota === null ? (
                                    <span className="text-xl text-white animate-pulse">Yükleniyor...</span>
                                ) : (
                                    <span className={`text-3xl font-black ${quota > 0 ? "text-[var(--color-b-yellow)]" : "text-red-500"}`}>
                                        {quota}
                                    </span>
                                )}
                            </div>

                            <div className="flex justify-center gap-4">
                                <button 
                                    onClick={onClose}
                                    className="px-6 py-2 rounded-lg font-semibold border border-gray-600 text-gray-300 hover:bg-gray-800 transition-colors"
                                >
                                    Reddet
                                </button>
                                <button 
                                    onClick={handleAnalyze}
                                    disabled={quota === null || quota <= 0}
                                    className="px-6 py-2 rounded-lg font-bold bg-[var(--color-b-yellow)] text-black hover:bg-[#f0c929] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    ✨ Onayla
                                </button>
                            </div>
                        </div>
                    )}

                    {step === "LOADING" && (
                        <div className="flex flex-col items-center justify-center py-12">
                            <div className="animate-spin text-[var(--color-b-yellow)] mb-4">
                                <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2 animate-pulse">Broker Raporu Hazırlanıyor...</h3>
                            <p className="text-gray-400 text-sm">Piyasa koşulları ve indikatörler analiz ediliyor.</p>
                        </div>
                    )}

                    {step === "RESULT" && (
                        <div className="prose prose-invert max-w-none text-gray-300 ai-prose">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {resultText}
                            </ReactMarkdown>
                        </div>
                    )}

                    {step === "ERROR" && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
                            <div className="text-3xl mb-2">⚠️</div>
                            <p className="text-red-400">{errorText}</p>
                            <button onClick={onClose} className="mt-4 px-4 py-2 border border-red-500/50 text-red-400 rounded hover:bg-red-500/10">Kapat</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
