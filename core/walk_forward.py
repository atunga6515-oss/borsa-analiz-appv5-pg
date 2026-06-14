import pandas as pd

def walk_forward_vote(df: pd.DataFrame, buy_threshold: float = 55, sell_threshold: float = 55) -> dict:
    """
    Son 30-50 barda indikatör kırılımlarının başarı oranına göre al/sat oy yüzdelerini hesaplar.
    """
    if len(df) < 50:
        return {"buy_vote": 50.0, "sell_vote": 50.0}
        
    closes = df['Close'].values
    hits_buy = 0
    hits_sell = 0
    total_buy = 0
    total_sell = 0
    
    # Basit simülasyon: geçmişteki dönüşleri incele
    for i in range(len(closes) - 30, len(closes) - 5):
        # Yükseliş yönlü ivme (örnek: son 3 günde %2 düşmüş ama bugün toparlamış)
        if closes[i-1] < closes[i-2] and closes[i] > closes[i-1]:
            total_buy += 1
            if closes[i+5] > closes[i]:
                hits_buy += 1
                
        # Düşüş yönlü ivme
        if closes[i-1] > closes[i-2] and closes[i] < closes[i-1]:
            total_sell += 1
            if closes[i+5] < closes[i]:
                hits_sell += 1
                
    buy_vote = 50.0
    if total_buy > 0:
        buy_vote = (hits_buy / total_buy) * 100
        
    sell_vote = 50.0
    if total_sell > 0:
        sell_vote = (hits_sell / total_sell) * 100
        
    return {
        "buy_vote": round(buy_vote, 1),
        "sell_vote": round(sell_vote, 1)
    }
