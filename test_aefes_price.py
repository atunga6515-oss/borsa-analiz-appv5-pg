import yfinance as yf
tkr = yf.Ticker("AEFES.IS")
print(tkr.history(period="1d"))
