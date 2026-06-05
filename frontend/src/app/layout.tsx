import type { Metadata } from "next";
import "./globals.css";
import NavBar from "./NavBar";

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
                <NavBar />
                <main className="flex-1 flex overflow-hidden">{children}</main>
            </body>
        </html>
    );
}
