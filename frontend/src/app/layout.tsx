import type { Metadata } from "next";
import Link from 'next/link';
import "./globals.css";

export const metadata: Metadata = {
  title: "Borsa Terminali V5",
  description: "Profesyonel Hisse Senedi Analiz Terminali",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr">
      <body className="antialiased min-h-screen flex flex-col">
        {/* Navbar */}
        <header className="glass-header h-16 flex items-center px-6 sticky top-0 z-50 justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-[var(--color-b-yellow)] flex items-center justify-center font-bold text-[#181a20]">
                V5
              </div>
              <h1 className="text-xl font-bold text-white tracking-tight">Terminal</h1>
            </div>
            <nav className="hidden md:flex gap-6">
              <Link href="/" className="flex items-center gap-3 p-3 rounded bg-[var(--color-b-panel)] border border-[var(--color-b-border)] text-white hover:border-[var(--color-b-yellow)] hover:text-[var(--color-b-yellow)] transition-colors">
                <span className="text-lg">📊</span>
                <span className="font-medium">Piyasalar (Dashboard)</span>
              </Link>
              <Link href="/screener" className="flex items-center gap-3 p-3 rounded hover:bg-[var(--color-b-panel)] border border-transparent hover:border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white transition-colors">
                <span className="text-lg">⚡</span>
                <span className="font-medium">Screener (Al-Sat)</span>
              </Link>
              <Link href="/portfolio" className="flex items-center gap-3 p-3 rounded hover:bg-[var(--color-b-panel)] border border-transparent hover:border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white transition-colors">
                <span className="text-lg">💼</span>
                <span className="font-medium">Sanal Portföy</span>
              </Link>
              <Link href="/top-picks" className="flex items-center gap-2 p-2 rounded hover:bg-[var(--color-b-panel)] border border-transparent hover:border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white transition-colors text-sm">
                <span className="text-base">🎯</span>
                <span className="font-medium">Seçki</span>
              </Link>
              <Link href="/analysis" className="flex items-center gap-2 p-2 rounded hover:bg-[var(--color-b-panel)] border border-transparent hover:border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white transition-colors text-sm">
                <span className="text-base">🔬</span>
                <span className="font-medium">Analiz</span>
              </Link>
              <Link href="/kap" className="flex items-center gap-2 p-2 rounded hover:bg-[var(--color-b-panel)] border border-transparent hover:border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white transition-colors text-sm">
                <span className="text-base">📰</span>
                <span className="font-medium">KAP</span>
              </Link>
              <Link href="/backtest" className="flex items-center gap-2 p-2 rounded hover:bg-[var(--color-b-panel)] border border-transparent hover:border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white transition-colors text-sm">
                <span className="text-base">⚙️</span>
                <span className="font-medium">Backtest</span>
              </Link>
              <Link href="/strategy-compare" className="flex items-center gap-2 p-2 rounded hover:bg-[var(--color-b-panel)] border border-transparent hover:border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white transition-colors text-sm">
                <span className="text-base">🧪</span>
                <span className="font-medium">Kıyasla</span>
              </Link>
              <Link href="/risk" className="flex items-center gap-2 p-2 rounded hover:bg-[var(--color-b-panel)] border border-transparent hover:border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white transition-colors text-sm">
                <span className="text-base">⚠️</span>
                <span className="font-medium">Risk</span>
              </Link>
              <Link href="/alarms" className="flex items-center gap-2 p-2 rounded hover:bg-[var(--color-b-panel)] border border-transparent hover:border-[var(--color-b-border)] text-[var(--color-b-muted)] hover:text-white transition-colors text-sm">
                <span className="text-base">🔔</span>
                <span className="font-medium">Alarm</span>
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
             <Link href="/login" className="text-[var(--color-b-muted)] hover:text-white transition-colors text-sm font-medium">Giriş Yap</Link>
             <Link href="/login" className="bg-[var(--color-b-yellow)] text-[#181a20] px-4 py-1.5 rounded font-semibold text-sm hover:bg-[#f0c929] transition-colors">Kayıt Ol</Link>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 flex overflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
