"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import api from "@/lib/api";

export default function RegisterPage() {
    const [contactEmail, setContactEmail] = useState("bilgi@borsaterminali.com");

    useEffect(() => {
        api.get("/admin/settings").then((res) => {
            if (res.data?.settings?.contact_email) {
                setContactEmail(res.data.settings.contact_email);
            }
        }).catch(() => {});
    }, []);

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-[var(--color-b-bg)] relative overflow-hidden">
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-[var(--color-b-yellow)] opacity-5 rounded-full blur-3xl" />
                <div className="absolute bottom-1/3 left-1/4 w-64 h-64 bg-purple-500 opacity-5 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 w-full max-w-lg px-6">
                <div className="text-center mb-10">
                    <div className="inline-flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-[var(--color-b-yellow)] flex items-center justify-center font-black text-[#181a20] text-xl shadow-lg shadow-[rgba(252,213,53,0.3)]">
                            V5
                        </div>
                        <span className="text-3xl font-black text-white tracking-tight">Borsa Terminal</span>
                    </div>
                    <p className="text-[var(--color-b-muted)] text-sm">
                        Profesyonel Borsa Analiz Platformu
                    </p>
                </div>

                <div className="glass-panel p-8 rounded-2xl border border-[var(--color-b-border)] shadow-2xl text-center">
                    <h2 className="text-2xl font-bold text-white mb-4">Üyelik İşlemleri</h2>
                    
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-6 mb-6">
                        <p className="text-[var(--color-b-muted)] text-md leading-relaxed mb-4">
                            Borsa Analiz Terminali, kapalı devre çalışan profesyonel bir analiz platformudur. Dışarıdan otomatik kayıt alımı şu an için aktif değildir.
                        </p>
                        <p className="text-white font-medium text-lg mb-2">
                            Abonelik Paketleri ve Özellikleri
                        </p>
                        <p className="text-[var(--color-b-muted)] text-sm mb-4">
                            Çok yakında bu sayfa üzerinden platformun özelliklerini, abonelik paketlerimizi ve ücretlendirmeleri inceleyebileceksiniz.
                        </p>
                        <div className="bg-[#1e2329] p-4 rounded-xl border border-[var(--color-b-border)] inline-block">
                            <span className="block text-xs text-gray-500 mb-1">Kayıt ve İletişim İçin E-Posta Gönderin:</span>
                            <a href={`mailto:${contactEmail}`} className="text-[var(--color-b-yellow)] font-bold text-lg hover:underline">
                                {contactEmail}
                            </a>
                        </div>
                    </div>

                    <div className="mt-6 pt-6 border-t border-[var(--color-b-border)]">
                        <p className="text-[var(--color-b-muted)] text-sm">
                            Zaten hesabınız var mı?{" "}
                            <Link
                                href="/login"
                                className="text-[var(--color-b-yellow)] hover:underline font-semibold"
                            >
                                Giriş Yap
                            </Link>
                        </p>
                    </div>
                </div>

                <p className="text-center text-xs text-gray-700 mt-6">
                    Borsa Terminali V5 · Tüm hakları saklıdır.
                </p>
            </div>
        </div>
    );
}
