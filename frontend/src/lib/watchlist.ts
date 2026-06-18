import { toast } from "react-hot-toast";

const WATCHLIST_KEY = "custom_watchlist";
const MAX_STOCKS = 10;

export const getWatchlist = (): string[] => {
    if (typeof window === 'undefined') return [];
    try {
        const stored = localStorage.getItem(WATCHLIST_KEY);
        if (stored) {
            return JSON.parse(stored);
        }
    } catch (e) {
        console.error("Watchlist okuma hatası:", e);
    }
    return [];
};

export const addTickerToWatchlist = (ticker: string) => {
    const list = getWatchlist();
    const formattedTicker = ticker.trim().toUpperCase();
    
    if (!formattedTicker) return false;

    // Optional: Auto append .IS if it doesn't exist
    const fullTicker = formattedTicker.includes('.') ? formattedTicker : `${formattedTicker}.IS`;

    if (list.includes(fullTicker)) {
        toast.error(`${fullTicker} zaten izleme listesinde!`);
        return false;
    }

    if (list.length >= MAX_STOCKS) {
        toast.error(`Maksimum hisse sınırına ulaştınız (${MAX_STOCKS}).`);
        return false;
    }

    list.push(fullTicker);
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
    window.dispatchEvent(new Event("watchlist_updated"));
    toast.success(`${fullTicker} Göstergelere eklendi.`);
    return true;
};

export const removeTickerFromWatchlist = (ticker: string) => {
    const list = getWatchlist();
    const updated = list.filter(t => t !== ticker);
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(updated));
    window.dispatchEvent(new Event("watchlist_updated"));
};
