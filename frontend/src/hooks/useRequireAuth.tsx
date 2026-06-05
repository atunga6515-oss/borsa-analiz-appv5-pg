"use client";
import { useState, useCallback } from "react";
import Link from "next/link";

// ── Modal bileşeni ─────────────────────────────────────────────────────────
function LoginRequiredModal({ onClose }: { onClose: () => void }) {
    return (
        <div
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div className="glass-panel w-full max-w-sm mx-4 p-8 rounded-2xl border border-[var(--color-b-border)] shadow-2xl text-center relative">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-[var(--color-b-muted)] hover:text-white transition-colors text-xl"
                >
                    ✕
                </button>

                {/* İkon */}
                <div className="w-16 h-16 rounded-full bg-[var(--color-b-yellow)]/10 border border-[var(--color-b-yellow)]/30 flex items-center justify-center text-3xl mx-auto mb-5">
                    🔒
                </div>

                <h2 className="text-xl font-black text-white mb-2">Giriş Gerekli</h2>
                <p className="text-[var(--color-b-muted)] text-sm mb-6 leading-relaxed">
                    Bu özelliği kullanmak için hesabınıza giriş yapmanız gerekmektedir.
                    Ücretsiz kayıt olabilirsiniz.
                </p>

                <div className="flex flex-col gap-3">
                    <Link
                        href="/login"
                        className="w-full py-3 bg-[var(--color-b-yellow)] text-[#181a20] font-bold rounded-lg hover:bg-[#f0c929] transition-colors text-sm shadow-lg shadow-[rgba(252,213,53,0.2)]"
                    >
                        Giriş Yap →
                    </Link>
                    <Link
                        href="/register"
                        className="w-full py-3 bg-transparent border border-[var(--color-b-border)] text-[var(--color-b-muted)] font-medium rounded-lg hover:border-white/30 hover:text-white transition-colors text-sm"
                    >
                        Hesap Oluştur
                    </Link>
                </div>
            </div>
        </div>
    );
}

// ── Hook ───────────────────────────────────────────────────────────────────
/**
 * Kullanım:
 *   const { requireAuth, AuthModal } = useRequireAuth();
 *   <button onClick={() => requireAuth(handleScan)}>Tara</button>
 *   <AuthModal />
 */
export function useRequireAuth() {
    const [modalOpen, setModalOpen] = useState(false);

    const isLoggedIn = useCallback(() => {
        if (typeof window === "undefined") return false;
        return !!localStorage.getItem("token");
    }, []);

    const requireAuth = useCallback(
        (action: () => void) => {
            if (isLoggedIn()) {
                action();
            } else {
                setModalOpen(true);
            }
        },
        [isLoggedIn]
    );

    const AuthModal = modalOpen
        ? () => <LoginRequiredModal onClose={() => setModalOpen(false)} />
        : () => null;

    return { requireAuth, AuthModal, isLoggedIn };
}
