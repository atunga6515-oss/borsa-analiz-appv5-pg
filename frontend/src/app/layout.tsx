import type { Metadata } from "next";
import "./globals.css";
import NavBar from "./NavBar";
import { Toaster } from 'react-hot-toast';

export const metadata: Metadata = {
    title: "AlfaBIST | Akıllı Borsa Analizi",
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
                <NavBar />
                <main className="flex-1 flex overflow-hidden">{children}</main>
                <Toaster position="bottom-right" toastOptions={{ style: { background: '#333', color: '#fff' } }} />
            </body>
        </html>
    );
}
