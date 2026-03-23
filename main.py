import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.model_selection import TimeSeriesSplit, ParameterGrid
import matplotlib.pyplot as plt

# --- Market Data Loader ---
def get_market_data(symbol, start_date="2020-01-01", end_date=None):
    df = yf.download(symbol, start=start_date, end=end_date)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df = df.dropna()
    return df

# --- Risk Manager ---
class RiskManager:
    def __init__(self, stop_loss_pct=0.05, take_profit_pct=0.1, volatility_target=0.02):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.volatility_target = volatility_target

    def check_exit(self, entry_price, current_price):
        if current_price <= entry_price * (1 - self.stop_loss_pct):
            return 'stop_loss'
        return None

    def position_size(self, volatility):
        # Volatility targeting position sizing
        if volatility == 0 or np.isnan(volatility):
            return 0
        return min(1, self.volatility_target / volatility)

# --- Technical Indicators ---
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def add_indicators(df):
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(window=14).std()
    df['ATR'] = df['High'] - df['Low']
    df['ATR_MA'] = df['ATR'].rolling(window=14).mean()
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['RSI'] = compute_rsi(df['Close'], 14)
    df['BB_MA'] = df['Close'].rolling(window=20).mean()
    rolling_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_MA'] + 2 * rolling_std
    df['BB_Lower'] = df['BB_MA'] - 2 * rolling_std
    for lag in range(1, 4):
        df[f'Returns_lag{lag}'] = df['Returns'].shift(lag)
    return df
# --- Signal Generation ---
def generate_signals(df, rsi_low=30, rsi_high=70):
    # momentum strategy — trade WITH the trend, not against it
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    
    # buy when fast MA crosses above slow MA (uptrend starting)
    # sell when fast MA crosses below slow MA (downtrend starting)
    df['Signal_Long'] = (
        (df['MA20'] > df['MA50']) &
        (df['MA20'].shift(1) <= df['MA50'].shift(1))  # crossover moment
    )
    df['Signal_Short'] = (
        (df['MA20'] < df['MA50']) &
        (df['MA20'].shift(1) >= df['MA50'].shift(1))  # crossunder moment
    )
    return df

# --- Backtesting with Walk-Forward Validation ---
def backtest(df, fee_rate=0.001, slippage=0.0005, risk_manager=None):
    position = 0
    entry_price = 0
    returns = []
    sizes = []
    for idx, row in df.iterrows():
        size = 1
        if risk_manager:
            size = risk_manager.position_size(row['Volatility'])
        if position == 0:
            if row['Signal_Long']:
                position = 1
                entry_price = row['Close'] * (1 + slippage)
                sizes.append(size)
            elif row['Signal_Short']:
                position = -1
                entry_price = row['Close'] * (1 - slippage)
                sizes.append(size)
            else:
                sizes.append(0)
        else:
            exit_reason = risk_manager.check_exit(entry_price, row['Close']) if risk_manager else None
            if (position == 1 and (row['Signal_Short'] or exit_reason)) or \
               (position == -1 and (row['Signal_Long'] or exit_reason)):
                pnl = (row['Close'] - entry_price) / entry_price * position * size
                pnl -= fee_rate
                returns.append(pnl)
                position = 0
                sizes.append(0)
            else:
                returns.append(0)
                sizes.append(size)
    df['Strategy_Returns'] = pd.Series(returns + [0]*(len(df)-len(returns)), index=df.index)
    df['Position_Size'] = sizes
    return df

# --- Performance Metrics ---
def performance_metrics(df):
    strat_ret = df['Strategy_Returns'].dropna()
    # only look at rows where a trade actually closed
    trades = strat_ret[strat_ret != 0]
    if len(trades) == 0:
        print("No trades executed.")
        return
    sharpe = trades.mean() / trades.std() * np.sqrt(252)
    cum_ret = (1 + strat_ret).cumprod()
    max_dd = (cum_ret / cum_ret.cummax() - 1).min()
    win_rate = (trades > 0).sum() / len(trades)
    profit_factor = trades[trades > 0].sum() / abs(trades[trades < 0].sum()) if len(trades[trades < 0]) > 0 else float('inf')
    print(f"Total Trades: {len(trades)}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print(f"Total Return: {cum_ret.iloc[-1] - 1:.2%}")
    print(f"Win Rate: {win_rate:.2%}")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Expectancy: {trades.mean():.4f}")

# --- Hyperparameter Optimization ---
def optimize_strategy(df):
    param_grid = {
        'stop_loss_pct': [0.03, 0.05, 0.07, 0.10, 0.15]
    }
    best_sharpe = -np.inf
    best_params = None
    for params in ParameterGrid(param_grid):
        risk_manager = RiskManager(stop_loss_pct=params['stop_loss_pct'])
        df2 = generate_signals(df.copy())
        df2 = backtest(df2, risk_manager=risk_manager)
        trades = df2['Strategy_Returns'][df2['Strategy_Returns'] != 0].dropna()
        if len(trades) < 5:
            continue
        sharpe = trades.mean() / trades.std() * np.sqrt(252)
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = params
    print(f"Best Params: {best_params}, Best Sharpe: {best_sharpe:.2f}")
    return best_params

# --- Main Pipeline ---
def main():
    data = get_market_data("BTC-USD", start_date="2022-01-01")
    data = add_indicators(data)
    best_params = optimize_strategy(data)
    risk_manager = RiskManager(stop_loss_pct=best_params['stop_loss_pct'])
    data = generate_signals(data)
    data = backtest(data, risk_manager=risk_manager)
    performance_metrics(data)
    # Visualization
    plt.figure(figsize=(12,6))
    (1 + data['Strategy_Returns'].fillna(0)).cumprod().plot(label='Strategy')
    (data['Close'] / data['Close'].iloc[0]).plot(label='Buy & Hold')
    plt.legend()
    plt.title('Strategy vs Buy & Hold')
    plt.show()

if __name__ == "__main__":
    main()