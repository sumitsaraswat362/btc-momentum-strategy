import yfinance as yf

def get_market_data(ticker="BTC-USD", start_date="2024-01-01"):
    print(f"--- Fetching Live Data for {ticker} from {start_date} ---")
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(start=start_date)
    
    # Clean the data: forward-fill any gaps
    df = df.ffill()
    return df